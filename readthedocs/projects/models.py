"""Project models."""

import fnmatch
import logging
import os
import re
from shlex import quote
from urllib.parse import urlparse

from allauth.socialaccount.providers import registry as allauth_registry
from django.conf import settings
from django.conf.urls import include
from django.contrib.auth.models import User
from django.core.files.storage import get_storage_class
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Prefetch
from django.urls import re_path, reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views import defaults
from django_extensions.db.fields import CreationDateTimeField
from django_extensions.db.models import TimeStampedModel
from taggit.managers import TaggableManager

from readthedocs.api.v2.client import api
from readthedocs.builds.constants import EXTERNAL, INTERNAL, LATEST, STABLE
from readthedocs.constants import pattern_opts
from readthedocs.core.resolver import resolve, resolve_domain
from readthedocs.core.utils import slugify
from readthedocs.doc_builder.constants import DOCKER_LIMITS
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.managers import HTMLFileManager
from readthedocs.projects.querysets import (
    ChildRelatedProjectQuerySet,
    FeatureQuerySet,
    HTMLFileQuerySet,
    ProjectQuerySet,
    RelatedProjectQuerySet,
)
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.projects.validators import (
    validate_domain_name,
    validate_repository_url,
)
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.search.parsers import MkDocsParser, SphinxParser
from readthedocs.vcs_support.backends import backend_cls
from readthedocs.vcs_support.utils import Lock, NonBlockingLock

from .constants import (
    MEDIA_TYPE_EPUB,
    MEDIA_TYPE_HTMLZIP,
    MEDIA_TYPE_PDF,
    MEDIA_TYPES,
)

log = logging.getLogger(__name__)


class ProjectRelationship(models.Model):

    """
    Project to project relationship.

    This is used for subprojects
    """

    parent = models.ForeignKey(
        'projects.Project',
        verbose_name=_('Parent'),
        related_name='subprojects',
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        'projects.Project',
        verbose_name=_('Child'),
        related_name='superprojects',
        on_delete=models.CASCADE,
    )
    alias = models.SlugField(
        _('Alias'),
        max_length=255,
        null=True,
        blank=True,
        db_index=False,
    )

    objects = ChildRelatedProjectQuerySet.as_manager()

    def __str__(self):
        return '{} -> {}'.format(self.parent, self.child)

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        if not self.alias:
            self.alias = self.child.slug
        super().save(*args, **kwargs)

    # HACK
    def get_absolute_url(self):
        return resolve(self.child)


class Project(models.Model):

    """Project model."""

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Generally from conf.py
    users = models.ManyToManyField(
        User,
        verbose_name=_('User'),
        related_name='projects',
    )
    # A DNS label can contain up to 63 characters.
    name = models.CharField(_('Name'), max_length=63)
    slug = models.SlugField(_('Slug'), max_length=63, unique=True)
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Short description of this project'),
    )
    repo = models.CharField(
        _('Repository URL'),
        max_length=255,
        validators=[validate_repository_url],
        help_text=_('Hosted documentation repository URL'),
        db_index=True,
    )
    repo_type = models.CharField(
        _('Repository type'),
        max_length=10,
        choices=constants.REPO_CHOICES,
        default='git',
    )
    project_url = models.URLField(
        _('Project homepage'),
        blank=True,
        help_text=_('The project\'s homepage'),
    )
    canonical_url = models.URLField(
        _('Canonical URL'),
        blank=True,
        help_text=_('URL that documentation is expected to serve from'),
    )
    single_version = models.BooleanField(
        _('Single version'),
        default=False,
        help_text=_(
            'A single version site has no translations and only your '
            '"latest" version, served at the root of the domain. Use '
            'this with caution, only turn it on if you will <b>never</b> '
            'have multiple versions of your docs.',
        ),
    )
    default_version = models.CharField(
        _('Default version'),
        max_length=255,
        default=LATEST,
        help_text=_('The version of your project that / redirects to'),
    )
    # In default_branch, None means the backend should choose the
    # appropriate branch. Eg 'master' for git
    default_branch = models.CharField(
        _('Default branch'),
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'What branch "latest" points to. Leave empty '
            'to use the default value for your VCS (eg. '
            '<code>trunk</code> or <code>master</code>).',
        ),
    )
    requirements_file = models.CharField(
        _('Requirements file'),
        max_length=255,
        default=None,
        null=True,
        blank=True,
        help_text=_(
            'A <a '
            'href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">'
            'pip requirements file</a> needed to build your documentation. '
            'Path from the root of your project.',
        ),
    )
    documentation_type = models.CharField(
        _('Documentation type'),
        max_length=20,
        choices=constants.DOCUMENTATION_CHOICES,
        default='sphinx',
        help_text=_(
            'Type of documentation you are building. <a href="'
            'http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html.'
            'DirectoryHTMLBuilder">More info on sphinx builders</a>.',
        ),
    )
    urlconf = models.CharField(
        _('Documentation URL Configuration'),
        max_length=255,
        default=None,
        blank=True,
        null=True,
        help_text=_(
            'Supports the following keys: $language, $version, $subproject, $filename. '
            'An example: `$language/$version/$filename`.'
        ),
    )

    external_builds_enabled = models.BooleanField(
        _('Build pull requests for this project'),
        default=False,
        help_text=_('More information in <a href="https://docs.readthedocs.io/en/latest/guides/autobuild-docs-for-pull-requests.html">our docs</a>')  # noqa
    )

    # Project features
    cdn_enabled = models.BooleanField(_('CDN Enabled'), default=False)
    analytics_code = models.CharField(
        _('Analytics code'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_(
            'Google Analytics Tracking ID '
            '(ex. <code>UA-22345342-1</code>). '
            'This may slow down your page loads.',
        ),
    )
    analytics_disabled = models.BooleanField(
        _('Disable Analytics'),
        default=False,
        null=True,
        help_text=_(
            'Disable Google Analytics completely for this project '
            '(requires rebuilding documentation)',
        ),
    )
    container_image = models.CharField(
        _('Alternative container image'),
        max_length=64,
        null=True,
        blank=True,
    )
    container_mem_limit = models.CharField(
        _('Container memory limit'),
        max_length=10,
        null=True,
        blank=True,
        help_text=_(
            'Memory limit in Docker format '
            '-- example: <code>512m</code> or <code>1g</code>',
        ),
    )
    container_time_limit = models.IntegerField(
        _('Container time limit in seconds'),
        null=True,
        blank=True,
    )
    build_queue = models.CharField(
        _('Alternate build queue id'),
        max_length=32,
        null=True,
        blank=True,
    )
    max_concurrent_builds = models.IntegerField(
        _('Maximum concurrent builds allowed for this project'),
        null=True,
        blank=True,
    )
    allow_promos = models.BooleanField(
        _('Allow paid advertising'),
        default=True,
        help_text=_('If unchecked, users will still see community ads.'),
    )
    ad_free = models.BooleanField(
        _('Ad-free'),
        default=False,
        help_text='If checked, do not show advertising for this project',
    )
    show_version_warning = models.BooleanField(
        _('Show version warning'),
        default=False,
        help_text=_('Show warning banner in non-stable nor latest versions.'),
    )

    # Sphinx specific build options.
    enable_epub_build = models.BooleanField(
        _('Enable EPUB build'),
        default=True,
        help_text=_(
            'Create a EPUB version of your documentation with each build.',
        ),
    )
    enable_pdf_build = models.BooleanField(
        _('Enable PDF build'),
        default=True,
        help_text=_(
            'Create a PDF version of your documentation with each build.',
        ),
    )

    # Other model data.
    path = models.CharField(
        _('Path'),
        max_length=255,
        editable=False,
        help_text=_(
            'The directory where '
            '<code>conf.py</code> lives',
        ),
    )
    conf_py_file = models.CharField(
        _('Python configuration file'),
        max_length=255,
        default='',
        blank=True,
        help_text=_(
            'Path from project root to <code>conf.py</code> file '
            '(ex. <code>docs/conf.py</code>). '
            'Leave blank if you want us to find it for you.',
        ),
    )

    featured = models.BooleanField(_('Featured'), default=False)
    skip = models.BooleanField(_('Skip'), default=False)
    install_project = models.BooleanField(
        _('Install Project'),
        help_text=_(
            'Install your project inside a virtualenv using <code>setup.py '
            'install</code>',
        ),
        default=False,
    )

    # This model attribute holds the python interpreter used to create the
    # virtual environment
    python_interpreter = models.CharField(
        _('Python Interpreter'),
        max_length=20,
        choices=constants.PYTHON_CHOICES,
        default='python3',
        help_text=_(
            'The Python interpreter used to create the virtual '
            'environment.',
        ),
    )

    use_system_packages = models.BooleanField(
        _('Use system packages'),
        help_text=_(
            'Give the virtual environment access to the global '
            'site-packages dir.',
        ),
        default=False,
    )
    privacy_level = models.CharField(
        _('Privacy Level'),
        max_length=20,
        choices=constants.PRIVACY_CHOICES,
        default=settings.DEFAULT_PRIVACY_LEVEL,
        help_text=_(
            'Level of privacy that you want on the repository.',
        ),
    )

    # Subprojects
    related_projects = models.ManyToManyField(
        'self',
        verbose_name=_('Related projects'),
        blank=True,
        symmetrical=False,
        through=ProjectRelationship,
    )

    # Language bits
    language = models.CharField(
        _('Language'),
        max_length=20,
        default='en',
        help_text=_(
            'The language the project '
            'documentation is rendered in. '
            "Note: this affects your project's URL.",
        ),
        choices=constants.LANGUAGES,
    )

    programming_language = models.CharField(
        _('Programming Language'),
        max_length=20,
        default='words',
        help_text=_(
            'The primary programming language the project is written in.',
        ),
        choices=constants.PROGRAMMING_LANGUAGES,
        blank=True,
    )
    # A subproject pointed at its main language, so it can be tracked
    main_language_project = models.ForeignKey(
        'self',
        related_name='translations',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    has_valid_webhook = models.BooleanField(
        default=False,
        help_text=_('This project has been built with a webhook'),
    )
    has_valid_clone = models.BooleanField(
        default=False,
        help_text=_('This project has been successfully cloned'),
    )

    tags = TaggableManager(blank=True)
    objects = ProjectQuerySet.as_manager()
    all_objects = models.Manager()

    # Property used for storing the latest build for a project when prefetching
    LATEST_BUILD_CACHE = '_latest_build'

    class Meta:
        ordering = ('slug',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        from readthedocs.projects import tasks
        first_save = self.pk is None
        if not self.slug:
            # Subdomains can't have underscores in them.
            self.slug = slugify(self.name)
            if not self.slug:
                raise Exception(_('Model must have slug'))
        super().save(*args, **kwargs)
        try:
            latest = self.versions.filter(slug=LATEST).first()
            default_branch = self.get_default_branch()
            if latest and latest.identifier != default_branch:
                latest.identifier = default_branch
                latest.save()
        except Exception:
            log.exception('Failed to update latest identifier')

        try:
            branch = self.get_default_branch()
            if not self.versions.filter(slug=LATEST).exists():
                self.versions.create_latest(identifier=branch)
        except Exception:
            log.exception('Error creating default branches')

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ
        from readthedocs.projects.tasks import clean_project_resources

        # Remove extra resources
        clean_project_resources(self)

        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None, lang_slug=None, external=False):
        """
        Return a URL for the docs.

        ``external`` defaults False because we only link external versions in very specific places
        """
        return resolve(
            project=self,
            version_slug=version_slug,
            language=lang_slug,
            external=external,
        )

    def get_builds_url(self):
        return reverse(
            'builds_project_list',
            kwargs={
                'project_slug': self.slug,
            },
        )

    def get_canonical_url(self):
        if settings.DONT_HIT_DB:
            return api.project(self.pk).canonical_url().get()['url']
        return self.get_docs_url()

    def get_subproject_urls(self):
        """
        List subproject URLs.

        This is used in search result linking
        """
        if settings.DONT_HIT_DB:
            return [(proj['slug'], proj['canonical_url']) for proj in
                    (api.project(self.pk).subprojects().get()['subprojects'])]
        return [(proj.child.slug, proj.child.get_docs_url())
                for proj in self.subprojects.all()]

    def get_storage_paths(self):
        """
        Get the paths of all artifacts used by the project.

        :return: the path to an item in storage
                 (can be used with ``storage.url`` to get the URL).
        """
        storage_paths = [
            f'{type_}/{self.slug}'
            for type_ in MEDIA_TYPES
        ]
        return storage_paths

    def get_storage_path(
            self,
            type_,
            version_slug=LATEST,
            include_file=True,
            version_type=None
    ):
        """
        Get a path to a build artifact for use with Django's storage system.

        :param type_: Media content type, ie - 'pdf', 'htmlzip'
        :param version_slug: Project version slug for lookup
        :param include_file: Include file name in return
        :param version_type: Project version type
        :return: the path to an item in storage
            (can be used with ``storage.url`` to get the URL)
        """
        type_dir = type_
        # Add `external/` prefix for external versions
        if version_type == EXTERNAL:
            type_dir = f'{EXTERNAL}/{type_}'

        folder_path = '{}/{}/{}'.format(
            type_dir,
            self.slug,
            version_slug,
        )
        if include_file:
            extension = type_.replace('htmlzip', 'zip')
            return '{}/{}.{}'.format(
                folder_path,
                self.slug,
                extension,
            )
        return folder_path

    def get_production_media_url(self, type_, version_slug):
        """Get the URL for downloading a specific media file."""
        # Use project domain for full path --same domain as docs
        # (project-slug.{PUBLIC_DOMAIN} or docs.project.com)
        domain = self.subdomain()

        # NOTE: we can't use ``reverse('project_download_media')`` here
        # because this URL only exists in El Proxito and this method is
        # accessed from Web instance

        if self.is_subproject:
            # docs.example.com/_/downloads/<alias>/<lang>/<ver>/pdf/
            path = f'//{domain}/{self.proxied_api_url}downloads/{self.alias}/{self.language}/{version_slug}/{type_}/'  # noqa
        else:
            # docs.example.com/_/downloads/<lang>/<ver>/pdf/
            path = f'//{domain}/{self.proxied_api_url}downloads/{self.language}/{version_slug}/{type_}/'  # noqa

        return path

    @property
    def proxied_api_host(self):
        """
        Used for the proxied_api_host in javascript.

        This needs to start with a slash at the root of the domain,
        and end without a slash
        """
        if self.urlconf:
            # Add our proxied api host at the first place we have a $variable
            # This supports both subpaths & normal root hosting
            url_prefix = self.urlconf.split('$', 1)[0]
            return '/' + url_prefix.strip('/') + '/_'
        return '/_'

    @property
    def proxied_api_url(self):
        """
        Like the api_host but for use as a URL prefix.

        It can't start with a /, but has to end with one.
        """
        return self.proxied_api_host.strip('/') + '/'

    @property
    def regex_urlconf(self):
        """
        Convert User's URLConf into a proper django URLConf.

        This replaces the user-facing syntax with the regex syntax.
        """
        to_convert = re.escape(self.urlconf)

        # We should standardize these names so we can loop over them easier
        to_convert = to_convert.replace(
            '\\$version',
            '(?P<version_slug>{regex})'.format(regex=pattern_opts['version_slug'])
        )
        to_convert = to_convert.replace(
            '\\$language',
            '(?P<lang_slug>{regex})'.format(regex=pattern_opts['lang_slug'])
        )
        to_convert = to_convert.replace(
            '\\$filename',
            '(?P<filename>{regex})'.format(regex=pattern_opts['filename_slug'])
        )
        to_convert = to_convert.replace(
            '\\$subproject',
            '(?P<subproject_slug>{regex})'.format(regex=pattern_opts['project_slug'])
        )

        if '\\$' in to_convert:
            log.warning(
                'Unconverted variable in a project URLConf: project=%s to_convert=%s',
                self, to_convert
            )
        return to_convert

    @property
    def proxito_urlconf(self):
        """
        Returns a URLConf class that is dynamically inserted via proxito.

        It is used for doc serving on projects that have their own ``urlconf``.
        """
        from readthedocs.projects.views.public import ProjectDownloadMedia
        from readthedocs.proxito.views.serve import ServeDocs
        from readthedocs.proxito.views.utils import proxito_404_page_handler
        from readthedocs.proxito.urls import core_urls

        class ProxitoURLConf:

            """A URLConf dynamically inserted by Proxito."""

            proxied_urls = [
                re_path(
                    r'{proxied_api_url}api/v2/'.format(
                        proxied_api_url=re.escape(self.proxied_api_url),
                    ),
                    include('readthedocs.api.v2.proxied_urls'),
                    name='user_proxied_api'
                ),
                re_path(
                    r'{proxied_api_url}downloads/'
                    r'(?P<lang_slug>{lang_slug})/'
                    r'(?P<version_slug>{version_slug})/'
                    r'(?P<type_>[-\w]+)/$'.format(
                        proxied_api_url=re.escape(self.proxied_api_url),
                        **pattern_opts),
                    ProjectDownloadMedia.as_view(same_domain_url=True),
                    name='user_proxied_downloads'
                ),
            ]
            docs_urls = [
                re_path(
                    '^{regex_urlconf}$'.format(regex_urlconf=self.regex_urlconf),
                    ServeDocs.as_view(),
                    name='user_proxied_serve_docs'
                ),
                # paths for redirects at the root
                re_path(
                    '^{proxied_api_url}$'.format(
                        proxied_api_url=re.escape(self.urlconf.split('$', 1)[0]),
                    ),
                    ServeDocs.as_view(),
                    name='user_proxied_serve_docs_subpath_redirect'
                ),
                re_path(
                    '^(?P<filename>{regex})$'.format(regex=pattern_opts['filename_slug']),
                    ServeDocs.as_view(),
                    name='user_proxied_serve_docs_root_redirect'
                ),
            ]
            urlpatterns = proxied_urls + core_urls + docs_urls
            handler404 = proxito_404_page_handler
            handler500 = defaults.server_error

        return ProxitoURLConf

    @property
    def is_subproject(self):
        """Return whether or not this project is a subproject."""
        return self.superprojects.exists()

    @property
    def alias(self):
        """Return the alias (as subproject) if it's a subproject."""  # noqa
        if self.is_subproject:
            return self.superprojects.first().alias

    def subdomain(self):
        """Get project subdomain from resolver."""
        return resolve_domain(self)

    def get_downloads(self):
        downloads = {}
        default_version = self.get_default_version()

        for type_ in ('htmlzip', 'epub', 'pdf'):
            downloads[type_] = self.get_production_media_url(
                type_,
                default_version,
            )

        return downloads

    @property
    def clean_repo(self):
        if self.repo.startswith('http://github.com'):
            return self.repo.replace('http://github.com', 'https://github.com')
        return self.repo

    # Doc PATH:
    # MEDIA_ROOT/slug/checkouts/version/<repo>

    @property
    def doc_path(self):
        return os.path.join(settings.DOCROOT, self.slug.replace('_', '-'))

    def checkout_path(self, version=LATEST):
        return os.path.join(self.doc_path, 'checkouts', version)

    @property
    def pip_cache_path(self):
        """Path to pip cache."""
        return os.path.join(self.doc_path, '.cache', 'pip')

    def full_doc_path(self, version=LATEST):
        """The path to the documentation root in the project."""
        doc_base = self.checkout_path(version)
        for possible_path in ['docs', 'doc', 'Doc']:
            if os.path.exists(os.path.join(doc_base, '%s' % possible_path)):
                return os.path.join(doc_base, '%s' % possible_path)
        # No docs directory, docs are at top-level.
        return doc_base

    def artifact_path(self, type_, version=LATEST):
        """The path to the build html docs in the project."""
        return os.path.join(self.doc_path, 'artifacts', version, type_)

    def full_build_path(self, version=LATEST):
        """The path to the build html docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'html')

    def full_latex_path(self, version=LATEST):
        """The path to the build LaTeX docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'latex')

    def full_epub_path(self, version=LATEST):
        """The path to the build epub docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'epub')

    # There is currently no support for building man/dash formats, but we keep
    # the support there for existing projects. They might have already existing
    # legacy builds.

    def full_man_path(self, version=LATEST):
        """The path to the build man docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'man')

    def full_dash_path(self, version=LATEST):
        """The path to the build dash docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'dash')

    def full_json_path(self, version=LATEST):
        """The path to the build json docs in the project."""
        json_path = os.path.join(self.conf_dir(version), '_build', 'json')
        return json_path

    def full_singlehtml_path(self, version=LATEST):
        """The path to the build singlehtml docs in the project."""
        return os.path.join(self.conf_dir(version), '_build', 'singlehtml')

    def rtd_build_path(self, version=LATEST):
        """The destination path where the built docs are copied."""
        return os.path.join(self.doc_path, 'rtd-builds', version)

    def static_metadata_path(self):
        """The path to the static metadata JSON settings file."""
        return os.path.join(self.doc_path, 'metadata.json')

    def conf_file(self, version=LATEST):
        """Find a ``conf.py`` file in the project checkout."""
        if self.conf_py_file:
            conf_path = os.path.join(
                self.checkout_path(version),
                self.conf_py_file,
            )

            if os.path.exists(conf_path):
                log.info('Inserting conf.py file path from model')
                return conf_path

            log.warning("Conf file specified on model doesn't exist")

        files = self.find('conf.py', version)
        if not files:
            files = self.full_find('conf.py', version)
        if len(files) == 1:
            return files[0]
        for filename in files:
            # When multiples conf.py files, we look up the first one that
            # contains the `doc` word in its path and return this one
            if filename.find('doc', 70) != -1:
                return filename

        # If the project has more than one conf.py file but none of them have
        # the `doc` word in the path, we raise an error informing this to the user
        if len(files) > 1:
            raise ProjectConfigurationError(
                ProjectConfigurationError.MULTIPLE_CONF_FILES,
            )

        raise ProjectConfigurationError(ProjectConfigurationError.NOT_FOUND)

    def conf_dir(self, version=LATEST):
        conf_file = self.conf_file(version)
        if conf_file:
            return os.path.dirname(conf_file)

    @property
    def has_good_build(self):
        # Check if there is `_good_build` annotation in the Queryset.
        # Used for Database optimization.
        if hasattr(self, '_good_build'):
            return self._good_build
        return self.builds(manager=INTERNAL).filter(success=True).exists()

    def has_media(self, type_, version_slug=LATEST, version_type=None):
        storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
        storage_path = self.get_storage_path(
            type_=type_, version_slug=version_slug,
            version_type=version_type
        )
        return storage.exists(storage_path)

    def has_pdf(self, version_slug=LATEST, version_type=None):
        return self.has_media(
            MEDIA_TYPE_PDF,
            version_slug=version_slug,
            version_type=version_type
        )

    def has_epub(self, version_slug=LATEST, version_type=None):
        return self.has_media(
            MEDIA_TYPE_EPUB,
            version_slug=version_slug,
            version_type=version_type
        )

    def has_htmlzip(self, version_slug=LATEST, version_type=None):
        return self.has_media(
            MEDIA_TYPE_HTMLZIP,
            version_slug=version_slug,
            version_type=version_type
        )

    def vcs_repo(
            self, version=LATEST, environment=None,
            verbose_name=None, version_type=None
    ):
        """
        Return a Backend object for this project able to handle VCS commands.

        :param environment: environment to run the commands
        :type environment: doc_builder.environments.BuildEnvironment
        :param version: version slug for the backend (``LATEST`` by default)
        :type version: str
        """
        # TODO: this seems to be the only method that receives a
        # ``version.slug`` instead of a ``Version`` instance (I prefer an
        # instance here)

        backend = self.vcs_class()
        if not backend:
            repo = None
        else:
            repo = backend(
                self, version, environment=environment,
                verbose_name=verbose_name, version_type=version_type
            )
        return repo

    def vcs_class(self):
        """
        Get the class used for VCS operations.

        This is useful when doing operations that don't need to have the repository on disk.
        """
        return backend_cls.get(self.repo_type)

    def git_service_class(self):
        """Get the service class for project. e.g: GitHubService, GitLabService."""
        from readthedocs.oauth.services import registry

        for service_cls in registry:
            if service_cls.is_project_service(self):
                service = service_cls
                break
        else:
            log.warning('There are no registered services in the application.')
            service = None

        return service

    @property
    def git_provider_name(self):
        """Get the provider name for project. e.g: GitHub, GitLab, BitBucket."""
        service = self.git_service_class()
        if service:
            provider = allauth_registry.by_id(service.adapter.provider_id)
            return provider.name
        return None

    def repo_nonblockinglock(self, version, max_lock_age=None):
        """
        Return a ``NonBlockingLock`` to acquire the lock via context manager.

        :param version: project's version that want to get the lock for.
        :param max_lock_age: time (in seconds) to consider the lock's age is old
            and grab it anyway. It default to the ``container_time_limit`` of
            the project or the default ``DOCKER_LIMITS['time']`` or
            ``REPO_LOCK_SECONDS`` or 30
        """
        if max_lock_age is None:
            max_lock_age = (
                self.container_time_limit or
                DOCKER_LIMITS.get('time') or
                settings.REPO_LOCK_SECONDS
            )

        return NonBlockingLock(
            project=self,
            version=version,
            max_lock_age=max_lock_age,
        )

    def repo_lock(self, version, timeout=5, polling_interval=5):
        return Lock(self, version, timeout, polling_interval)

    def find(self, filename, version):
        """
        Find files inside the project's ``doc`` path.

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.full_doc_path(version)):
            for match in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, match))
        return matches

    def full_find(self, filename, version):
        """
        Find files inside a project's checkout path.

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.checkout_path(version)):
            for match in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, match))
        return matches

    def get_latest_build(self, finished=True):
        """
        Get latest build for project.

        :param finished: Return only builds that are in a finished state
        """
        # Check if there is `_latest_build` attribute in the Queryset.
        # Used for Database optimization.
        if hasattr(self, self.LATEST_BUILD_CACHE):
            if self._latest_build:
                return self._latest_build[0]
            return None

        kwargs = {'type': 'html'}
        if finished:
            kwargs['state'] = 'finished'
        return self.builds(manager=INTERNAL).filter(**kwargs).first()

    def api_versions(self):
        from readthedocs.builds.models import APIVersion
        ret = []
        for version_data in api.project(self.pk).active_versions.get()['versions']:
            version = APIVersion(**version_data)
            ret.append(version)
        return sort_version_aware(ret)

    def active_versions(self):
        from readthedocs.builds.models import Version
        versions = Version.internal.public(project=self, only_active=True)
        return (
            versions.filter(built=True, active=True) |
            versions.filter(active=True, uploaded=True)
        )

    def ordered_active_versions(self, **kwargs):
        """
        Get all active versions, sorted.

        :param kwargs: All kwargs are passed down to the
                       `Version.internal.public` queryset.
        """
        from readthedocs.builds.models import Version
        kwargs.update(
            {
                'project': self,
                'only_active': True,
                'only_built': True,
            },
        )
        versions = (
            Version.internal.public(**kwargs)
            .select_related(
                'project',
                'project__main_language_project',
            )
            .prefetch_related(
                Prefetch(
                    'project__superprojects',
                    ProjectRelationship.objects.all().select_related('parent'),
                    to_attr='_superprojects',
                ),
                Prefetch(
                    'project__domains',
                    Domain.objects.filter(canonical=True),
                    to_attr='_canonical_domains',
                ),
            )
        )
        return sort_version_aware(versions)

    def all_active_versions(self):
        """
        Get queryset with all active versions.

        .. note::
            This is a temporary workaround for activate_versions filtering out
            things that were active, but failed to build

        :returns: :py:class:`Version` queryset
        """
        return self.versions(manager=INTERNAL).filter(active=True)

    def get_stable_version(self):
        return self.versions.filter(slug=STABLE).first()

    def update_stable_version(self):
        """
        Returns the version that was promoted to be the new stable version.

        Return ``None`` if no update was made or if there is no version on the
        project that can be considered stable.
        """

        # return immediately if the current stable is managed by the user and
        # not automatically by Read the Docs (``machine=False``)
        current_stable = self.get_stable_version()
        if current_stable and not current_stable.machine:
            return None

        versions = self.versions(manager=INTERNAL).all()
        new_stable = determine_stable_version(versions)
        if new_stable:
            if current_stable:
                identifier_updated = (
                    new_stable.identifier != current_stable.identifier
                )
                if identifier_updated:
                    log.info(
                        'Update stable version: %(project)s:%(version)s',
                        {
                            'project': self.slug,
                            'version': new_stable.identifier,
                        }
                    )
                    current_stable.identifier = new_stable.identifier
                    current_stable.save()
                    return new_stable
            else:
                log.info(
                    'Creating new stable version: %(project)s:%(version)s',
                    {
                        'project': self.slug,
                        'version': new_stable.identifier,
                    }
                )
                current_stable = self.versions.create_stable(
                    type=new_stable.type,
                    identifier=new_stable.identifier,
                )
                return new_stable

    def versions_from_branch_name(self, branch):
        return (
            self.versions.filter(identifier=branch) |
            self.versions.filter(identifier='remotes/origin/%s' % branch) |
            self.versions.filter(identifier='origin/%s' % branch) |
            self.versions.filter(verbose_name=branch)
        )

    def get_default_version(self):
        """
        Get the default version (slug).

        Returns self.default_version if the version with that slug actually
        exists (is built and published). Otherwise returns 'latest'.
        """
        # latest is a special case where we don't have to check if it exists
        if self.default_version == LATEST:
            return self.default_version
        # check if the default_version exists
        version_qs = self.versions.filter(
            slug=self.default_version,
            active=True,
        )
        if version_qs.exists():
            return self.default_version
        return LATEST

    def get_default_branch(self):
        """Get the version representing 'latest'."""
        if self.default_branch:
            return self.default_branch
        return self.vcs_class().fallback_branch

    def add_subproject(self, child, alias=None):
        subproject, __ = ProjectRelationship.objects.get_or_create(
            parent=self,
            child=child,
            alias=alias,
        )
        return subproject

    def remove_subproject(self, child):
        ProjectRelationship.objects.filter(parent=self, child=child).delete()

    def get_parent_relationship(self):
        """
        Get parent project relationship.

        It returns ``None`` if this is a top level project.
        """
        if hasattr(self, '_superprojects'):
            # Cached parent project relationship
            if self._superprojects:
                return self._superprojects[0]
            return None

        return self.superprojects.select_related('parent').first()

    def get_canonical_custom_domain(self):
        """Get the canonical custom domain or None."""
        if hasattr(self, '_canonical_domains'):
            # Cached custom domains
            if self._canonical_domains:
                return self._canonical_domains[0]
            return None

        return self.domains.filter(canonical=True).first()

    @property
    def features(self):
        return Feature.objects.for_project(self)

    def has_feature(self, feature_id):
        """
        Does project have existing feature flag.

        If the feature has a historical True value before the feature was added,
        we consider the project to have the flag. This is used for deprecating a
        feature or changing behavior for new projects
        """
        return self.features.filter(feature_id=feature_id).exists()

    def get_feature_value(self, feature, positive, negative):
        """
        Look up project feature, return corresponding value.

        If a project has a feature, return ``positive``, otherwise return
        ``negative``
        """
        return positive if self.has_feature(feature) else negative

    @property
    def show_advertising(self):
        """
        Whether this project is ad-free.

        :returns: ``True`` if advertising should be shown and ``False`` otherwise
        :rtype: bool
        """
        if self.ad_free or self.gold_owners.exists():
            return False

        return True

    @property
    def environment_variables(self):
        """
        Environment variables to build this particular project.

        :returns: dictionary with all the variables {name: value}
        :rtype: dict
        """
        return {
            variable.name: variable.value
            for variable in self.environmentvariable_set.all()
        }

    def is_valid_as_superproject(self, error_class):
        """
        Checks if the project can be a superproject.

        This is used to handle form and serializer validations
        if check fails returns ValidationError using to the error_class passed
        """
        # Check the parent project is not a subproject already
        if self.superprojects.exists():
            raise error_class(
                _('Subproject nesting is not supported'),
            )

    def is_valid_as_subproject(self, parent, error_class):
        """
        Checks if the project can be a subproject.

        This is used to handle form and serializer validations
        if check fails returns ValidationError using to the error_class passed
        """
        # Check the child project is not a subproject already
        if self.superprojects.exists():
            raise error_class(
                _('Child is already a subproject of another project'),
            )

        # Check the child project is already a superproject
        if self.subprojects.exists():
            raise error_class(
                _('Child is already a superproject'),
            )

        # Check the parent and child are not the same project
        if parent.slug == self.slug:
            raise error_class(
                _('Project can not be subproject of itself'),
            )


class APIProject(Project):

    """
    Project proxy model for API data deserialization.

    This replaces the pattern where API data was deserialized into a mocked
    :py:class:`Project` object. This pattern was confusing, as it was not explicit
    as to what form of object you were working with -- API backed or database
    backed.

    This model preserves the Project model methods, allowing for overrides on
    model field differences. This model pattern will generally only be used on
    builder instances, where we are interacting solely with API data.
    """

    features = []

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        self.features = kwargs.pop('features', [])
        environment_variables = kwargs.pop('environment_variables', {})
        ad_free = (not kwargs.pop('show_advertising', True))
        # These fields only exist on the API return, not on the model, so we'll
        # remove them to avoid throwing exceptions due to unexpected fields
        for key in ['users', 'resource_uri', 'absolute_url', 'downloads',
                    'main_language_project', 'related_projects']:
            try:
                del kwargs[key]
            except KeyError:
                pass
        super().__init__(*args, **kwargs)

        # Overwrite the database property with the value from the API
        self.ad_free = ad_free
        self._environment_variables = environment_variables

    def save(self, *args, **kwargs):
        return 0

    def has_feature(self, feature_id):
        return feature_id in self.features

    @property
    def show_advertising(self):
        """Whether this project is ad-free (don't access the database)."""
        return not self.ad_free

    @property
    def environment_variables(self):
        return self._environment_variables


class ImportedFile(models.Model):

    """
    Imported files model.

    This tracks files that are output from documentation builds, useful for
    things like CDN invalidation.
    """

    project = models.ForeignKey(
        Project,
        verbose_name=_('Project'),
        related_name='imported_files',
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        'builds.Version',
        verbose_name=_('Version'),
        related_name='imported_files',
        null=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'))

    # max_length is set to 4096 because linux has a maximum path length
    # of 4096 characters for most filesystems (including EXT4).
    # https://github.com/rtfd/readthedocs.org/issues/5061
    path = models.CharField(_('Path'), max_length=4096)
    md5 = models.CharField(_('MD5 checksum'), max_length=255)
    commit = models.CharField(_('Commit'), max_length=255)
    build = models.IntegerField(_('Build id'), null=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)
    rank = models.IntegerField(
        _('Page search rank'),
        default=0,
        validators=[MinValueValidator(-10), MaxValueValidator(10)],
    )
    ignore = models.BooleanField(
        _('Ignore this file from operations like indexing'),
        # default=False,
        # TODO: remove after migration
        null=True,
    )

    def get_absolute_url(self):
        return resolve(
            project=self.project,
            version_slug=self.version.slug,
            filename=self.path,
            # this should always be False because we don't have ImportedFile's for external versions
            external=False,
        )

    def __str__(self):
        return '{}: {}'.format(self.name, self.project)


class HTMLFile(ImportedFile):

    """
    Imported HTML file Proxy model.

    This tracks only the HTML files for indexing to search.
    """

    class Meta:
        proxy = True

    objects = HTMLFileManager.from_queryset(HTMLFileQuerySet)()

    def get_processed_json(self):
        parser_class = (
            SphinxParser if self.version.is_sphinx_type else MkDocsParser
        )
        parser = parser_class(self.version)
        return parser.parse(self.path)

    @cached_property
    def processed_json(self):
        return self.get_processed_json()


class Notification(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='%(class)s_notifications',
        on_delete=models.CASCADE,
    )
    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        abstract = True


class EmailHook(Notification):
    email = models.EmailField()

    def __str__(self):
        return self.email


class WebHook(Notification):
    url = models.URLField(
        max_length=600,
        help_text=_('URL to send the webhook to'),
    )

    def __str__(self):
        return self.url


class Domain(TimeStampedModel, models.Model):

    """A custom domain name for a project."""

    # TODO: Overridden from TimeStampedModel just to allow null values,
    # remove after deploy.
    created = CreationDateTimeField(
        _('created'),
        null=True,
        blank=True,
    )

    project = models.ForeignKey(
        Project,
        related_name='domains',
        on_delete=models.CASCADE,
    )
    domain = models.CharField(
        _('Domain'),
        unique=True,
        max_length=255,
        validators=[validate_domain_name],
    )
    machine = models.BooleanField(
        default=False,
        help_text=_('This Domain was auto-created'),
    )
    cname = models.BooleanField(
        default=False,
        help_text=_('This Domain is a CNAME for the project'),
    )
    canonical = models.BooleanField(
        default=False,
        help_text=_(
            'This Domain is the primary one where the documentation is '
            'served from',
        ),
    )
    https = models.BooleanField(
        _('Use HTTPS'),
        default=False,
        help_text=_('Always use HTTPS for this domain'),
    )
    count = models.IntegerField(
        default=0,
        help_text=_('Number of times this domain has been hit'),
    )

    # This is used in readthedocsext.
    ssl_status = models.CharField(
        _('SSL certificate status'),
        max_length=30,
        choices=constants.SSL_STATUS_CHOICES,
        default=constants.SSL_STATUS_UNKNOWN,
        # Remove after deploy
        null=True,
        blank=True,
    )

    # Strict-Transport-Security header options
    # These are not exposed to users because it's easy to misconfigure things
    # and hard to back out changes cleanly
    hsts_max_age = models.PositiveIntegerField(
        default=0,
        help_text=_('Set a custom max-age (eg. 31536000) for the HSTS header')
    )
    hsts_include_subdomains = models.BooleanField(
        default=False,
        help_text=_('If hsts_max_age > 0, set the includeSubDomains flag with the HSTS header')
    )
    hsts_preload = models.BooleanField(
        default=False,
        help_text=_('If hsts_max_age > 0, set the preload flag with the HSTS header')
    )

    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        ordering = ('-canonical', '-machine', 'domain')

    def __str__(self):
        return '{domain} pointed at {project}'.format(
            domain=self.domain,
            project=self.project.name,
        )

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        parsed = urlparse(self.domain)
        if parsed.scheme or parsed.netloc:
            self.domain = parsed.netloc
        else:
            self.domain = parsed.path
        super().save(*args, **kwargs)


class Feature(models.Model):

    """
    Project feature flags.

    Features should generally be added here as choices, however features may
    also be added dynamically from a signal in other packages. Features can be
    added by external packages with the use of signals::

        @receiver(pre_init, sender=Feature)
        def add_features(sender, **kwargs):
            sender.FEATURES += (('blah', 'BLAH'),)

    The FeatureForm will grab the updated list on instantiation.
    """

    # Feature constants - this is not a exhaustive list of features, features
    # may be added by other packages
    USE_SPHINX_LATEST = 'use_sphinx_latest'
    DONT_INSTALL_DOCUTILS = 'dont_install_docutils'
    ALLOW_DEPRECATED_WEBHOOKS = 'allow_deprecated_webhooks'
    PIP_ALWAYS_UPGRADE = 'pip_always_upgrade'
    DONT_OVERWRITE_SPHINX_CONTEXT = 'dont_overwrite_sphinx_context'
    MKDOCS_THEME_RTD = 'mkdocs_theme_rtd'
    API_LARGE_DATA = 'api_large_data'
    DONT_SHALLOW_CLONE = 'dont_shallow_clone'
    USE_TESTING_BUILD_IMAGE = 'use_testing_build_image'
    SHARE_SPHINX_DOCTREE = 'share_sphinx_doctree'
    DEFAULT_TO_MKDOCS_0_17_3 = 'default_to_mkdocs_0_17_3'
    CLEAN_AFTER_BUILD = 'clean_after_build'
    EXTERNAL_VERSION_BUILD = 'external_version_build'
    UPDATE_CONDA_STARTUP = 'update_conda_startup'
    CONDA_APPEND_CORE_REQUIREMENTS = 'conda_append_core_requirements'
    ALL_VERSIONS_IN_HTML_CONTEXT = 'all_versions_in_html_context'
    SKIP_SYNC_TAGS = 'skip_sync_tags'
    SKIP_SYNC_BRANCHES = 'skip_sync_branches'
    SKIP_SYNC_VERSIONS = 'skip_sync_versions'
    CACHED_ENVIRONMENT = 'cached_environment'
    LIMIT_CONCURRENT_BUILDS = 'limit_concurrent_builds'
    DISABLE_SERVER_SIDE_SEARCH = 'disable_server_side_search'
    ENABLE_MKDOCS_SERVER_SIDE_SEARCH = 'enable_mkdocs_server_side_search'
    FORCE_SPHINX_FROM_VENV = 'force_sphinx_from_venv'
    LIST_PACKAGES_INSTALLED_ENV = 'list_packages_installed_env'
    VCS_REMOTE_LISTING = 'vcs_remote_listing'
    STORE_PAGEVIEWS = 'store_pageviews'
    SPHINX_PARALLEL = 'sphinx_parallel'
    USE_SPHINX_BUILDERS = 'use_sphinx_builders'
    DEDUPLICATE_BUILDS = 'deduplicate_builds'
    USE_SPHINX_RTD_EXT_LATEST = 'rtd_sphinx_ext_latest'
    DEFAULT_TO_FUZZY_SEARCH = 'default_to_fuzzy_search'
    INDEX_FROM_HTML_FILES = 'index_from_html_files'
    DONT_CREATE_INDEX = 'dont_create_index'
    USE_NEW_PIP_RESOLVER = 'use_new_pip_resolver'

    FEATURES = (
        (USE_SPHINX_LATEST, _('Use latest version of Sphinx')),
        (
            DONT_INSTALL_DOCUTILS,
            _(
                'Do not install docutils as requirement for build documentation',
            ),
        ),
        (ALLOW_DEPRECATED_WEBHOOKS, _('Allow deprecated webhook views')),
        (PIP_ALWAYS_UPGRADE, _('Always run pip install --upgrade')),
        (
            DONT_OVERWRITE_SPHINX_CONTEXT,
            _(
                'Do not overwrite context vars in conf.py with Read the Docs context',
            ),
        ),
        (
            MKDOCS_THEME_RTD,
            _('Use Read the Docs theme for MkDocs as default theme'),
        ),
        (
            DONT_SHALLOW_CLONE,
            _('Do not shallow clone when cloning git repos'),
        ),
        (
            USE_TESTING_BUILD_IMAGE,
            _('Use Docker image labelled as `testing` to build the docs'),
        ),
        (
            API_LARGE_DATA,
            _('Try alternative method of posting large data'),
        ),
        (
            SHARE_SPHINX_DOCTREE,
            _('Use shared directory for doctrees'),
        ),
        (
            DEFAULT_TO_MKDOCS_0_17_3,
            _('Install mkdocs 0.17.3 by default'),
        ),
        (
            CLEAN_AFTER_BUILD,
            _('Clean all files used in the build process'),
        ),
        (
            EXTERNAL_VERSION_BUILD,
            _('Enable project to build on pull/merge requests'),
        ),
        (
            UPDATE_CONDA_STARTUP,
            _('Upgrade conda before creating the environment'),
        ),
        (
            CONDA_APPEND_CORE_REQUIREMENTS,
            _('Append Read the Docs core requirements to environment.yml file'),
        ),
        (
            ALL_VERSIONS_IN_HTML_CONTEXT,
            _(
                'Pass all versions (including private) into the html context '
                'when building with Sphinx'
            ),
        ),
        (
            SKIP_SYNC_BRANCHES,
            _('Skip syncing branches'),
        ),
        (
            SKIP_SYNC_TAGS,
            _('Skip syncing tags'),
        ),
        (
            SKIP_SYNC_VERSIONS,
            _('Skip sync versions task'),
        ),
        (
            CACHED_ENVIRONMENT,
            _('Cache the environment (virtualenv, conda, pip cache, repository) in storage'),
        ),
        (
            LIMIT_CONCURRENT_BUILDS,
            _('Limit the amount of concurrent builds'),
        ),
        (
            DISABLE_SERVER_SIDE_SEARCH,
            _('Disable server side search'),
        ),
        (
            ENABLE_MKDOCS_SERVER_SIDE_SEARCH,
            _('Enable server side search for MkDocs projects'),
        ),
        (
            FORCE_SPHINX_FROM_VENV,
            _('Force to use Sphinx from the current virtual environment'),
        ),
        (
            LIST_PACKAGES_INSTALLED_ENV,
            _(
                'List packages installed in the environment ("pip list" or "conda list") '
                'on build\'s output',
            ),
        ),
        (
            VCS_REMOTE_LISTING,
            _('Use remote listing in VCS (e.g. git ls-remote) if supported for sync versions'),
        ),
        (
            STORE_PAGEVIEWS,
            _('Store pageviews for this project'),
        ),
        (
            SPHINX_PARALLEL,
            _('Use "-j auto" when calling sphinx-build'),
        ),
        (
            USE_SPHINX_BUILDERS,
            _('Use regular sphinx builders instead of custom RTD builders'),
        ),
        (
            DEDUPLICATE_BUILDS,
            _('Mark duplicated builds as NOOP to be skipped by builders'),
        ),
        (
            USE_SPHINX_RTD_EXT_LATEST,
            _('Use latest version of the Read the Docs Sphinx extension'),
        ),
        (
            DEFAULT_TO_FUZZY_SEARCH,
            _('Default to fuzzy search for simple search queries'),
        ),
        (
            INDEX_FROM_HTML_FILES,
            _('Index content directly from html files instead or relying in other sources'),
        ),
        (
            DONT_CREATE_INDEX,
            _('Do not create index.md or README.rst if the project does not have one.'),
        ),
        (
            USE_NEW_PIP_RESOLVER,
            _('Use new pip resolver'),
        ),
    )

    projects = models.ManyToManyField(
        Project,
        blank=True,
    )
    # Feature is not implemented as a ChoiceField, as we don't want validation
    # at the database level on this field. Arbitrary values are allowed here.
    feature_id = models.CharField(
        _('Feature identifier'),
        max_length=32,
        unique=True,
    )
    add_date = models.DateTimeField(
        _('Date feature was added'),
        auto_now_add=True,
    )
    default_true = models.BooleanField(
        _('Historical default is True'),
        default=False,
    )

    objects = FeatureQuerySet.as_manager()

    def __str__(self):
        return '{} feature'.format(self.get_feature_display(),)

    def get_feature_display(self):
        """
        Implement display name field for fake ChoiceField.

        Because the field is not a ChoiceField here, we need to manually
        implement this behavior.
        """
        return dict(self.FEATURES).get(self.feature_id, self.feature_id)


class EnvironmentVariable(TimeStampedModel, models.Model):
    name = models.CharField(
        max_length=128,
        help_text=_('Name of the environment variable'),
    )
    value = models.CharField(
        max_length=2048,
        help_text=_('Value of the environment variable'),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        help_text=_('Project where this variable will be used'),
    )

    objects = RelatedProjectQuerySet.as_manager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        self.value = quote(self.value)
        return super().save(*args, **kwargs)
