"""Project models."""

import fnmatch
import logging
import os
import re
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import get_storage_class
from django.db import models
from django.db.models import Prefetch
from django.urls import NoReverseMatch, reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from guardian.shortcuts import assign
from six.moves import shlex_quote
from taggit.managers import TaggableManager

from readthedocs.api.v2.client import api
from readthedocs.builds.constants import LATEST, STABLE
from readthedocs.core.resolver import resolve, resolve_domain
from readthedocs.core.utils import broadcast, slugify
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.managers import HTMLFileManager
from readthedocs.projects.querysets import (
    ChildRelatedProjectQuerySet,
    FeatureQuerySet,
    ProjectQuerySet,
    RelatedProjectQuerySet,
)
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.projects.validators import (
    validate_domain_name,
    validate_repository_url,
)
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.search.parse_json import process_file
from readthedocs.vcs_support.backends import backend_cls
from readthedocs.vcs_support.utils import Lock, NonBlockingLock

from .constants import (
    MEDIA_TYPES,
    MEDIA_TYPE_PDF,
    MEDIA_TYPE_EPUB,
    MEDIA_TYPE_HTMLZIP,
)


log = logging.getLogger(__name__)


class ProjectRelationship(models.Model):

    """
    Project to project relationship.

    This is used for subprojects
    """

    parent = models.ForeignKey(
        'Project',
        verbose_name=_('Parent'),
        related_name='subprojects',
    )
    child = models.ForeignKey(
        'Project',
        verbose_name=_('Child'),
        related_name='superprojects',
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
        help_text=_(
            'The reStructuredText '
            'description of the project',
        ),
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
            'Level of privacy that you want on the repository. '
            'Protected means public but not in listings.',
        ),
    )
    version_privacy_level = models.CharField(
        _('Version Privacy Level'),
        max_length=20,
        choices=constants.PRIVACY_CHOICES,
        default=settings.DEFAULT_PRIVACY_LEVEL,
        help_text=_(
            'Default level of privacy you want on built '
            'versions of documentation.',
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

    class Meta:
        ordering = ('slug',)
        permissions = (
            # Translators: Permission around whether a user can view the
            # project
            ('view_project', _('View Project')),
        )

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
        for owner in self.users.all():
            assign('view_project', owner, self)
        try:
            latest = self.versions.filter(slug=LATEST).first()
            default_branch = self.get_default_branch()
            if latest and latest.identifier != default_branch:
                latest.identifier = default_branch
                latest.save()
        except Exception:
            log.exception('Failed to update latest identifier')

        try:
            if not first_save:
                log.info(
                    'Re-symlinking project and subprojects: project=%s',
                    self.slug,
                )
                broadcast(
                    type='app',
                    task=tasks.symlink_project,
                    args=[self.pk],
                )
                log.info(
                    'Re-symlinking superprojects: project=%s',
                    self.slug,
                )
                for relationship in self.superprojects.all():
                    broadcast(
                        type='app',
                        task=tasks.symlink_project,
                        args=[relationship.parent.pk],
                    )

        except Exception:
            log.exception('failed to symlink project')
        try:
            if not first_save:
                broadcast(
                    type='app',
                    task=tasks.update_static_metadata,
                    args=[self.pk],
                )
        except Exception:
            log.exception('failed to update static metadata')
        try:
            branch = self.default_branch or self.vcs_repo().fallback_branch
            if not self.versions.filter(slug=LATEST).exists():
                self.versions.create_latest(identifier=branch)
        except Exception:
            log.exception('Error creating default branches')

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ
        from readthedocs.projects import tasks

        # Remove local FS build artifacts on the web servers
        broadcast(
            type='app',
            task=tasks.remove_dirs,
            args=[(self.doc_path,)],
        )

        # Remove build artifacts from storage
        storage_paths = []
        for type_ in MEDIA_TYPES:
            storage_paths.append(
                '{}/{}'.format(
                    type_,
                    self.slug,
                )
            )
        tasks.remove_build_storage_paths.delay(storage_paths)

        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None, lang_slug=None, private=None):
        """
        Return a URL for the docs.

        Always use http for now, to avoid content warnings.
        """
        return resolve(
            project=self,
            version_slug=version_slug,
            language=lang_slug,
            private=private,
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

    def get_storage_path(self, type_, version_slug=LATEST, include_file=True):
        """
        Get a path to a build artifact for use with Django's storage system.

        :param type_: Media content type, ie - 'pdf', 'htmlzip'
        :param version_slug: Project version slug for lookup
        :param include_file: Include file name in return
        :return: the path to an item in storage
            (can be used with ``storage.url`` to get the URL)
        """
        folder_path = '{}/{}/{}'.format(
            type_,
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

    def get_production_media_path(self, type_, version_slug, include_file=True):
        """
        Used to see if these files exist so we can offer them for download.

        :param type_: Media content type, ie - 'pdf', 'zip'
        :param version_slug: Project version slug for lookup
        :param include_file: Include file name in return
        :type include_file: bool

        :returns: Full path to media file or path
        """
        if settings.DEFAULT_PRIVACY_LEVEL == 'public' or settings.DEBUG:
            path = os.path.join(
                settings.MEDIA_ROOT,
                type_,
                self.slug,
                version_slug,
            )
        else:
            path = os.path.join(
                settings.PRODUCTION_MEDIA_ARTIFACTS,
                type_,
                self.slug,
                version_slug,
            )
        if include_file:
            path = os.path.join(
                path,
                '{}.{}'.format(self.slug, type_.replace('htmlzip', 'zip')),
            )
        return path

    def get_production_media_url(self, type_, version_slug, full_path=True):
        """Get the URL for downloading a specific media file."""
        try:
            path = reverse(
                'project_download_media',
                kwargs={
                    'project_slug': self.slug,
                    'type_': type_,
                    'version_slug': version_slug,
                },
            )
        except NoReverseMatch:
            return ''
        if full_path:
            path = '//{}{}'.format(settings.PRODUCTION_DOMAIN, path)
        return path

    def subdomain(self):
        """Get project subdomain from resolver."""
        return resolve_domain(self)

    def get_downloads(self):
        downloads = {}
        downloads['htmlzip'] = self.get_production_media_url(
            'htmlzip',
            self.get_default_version(),
        )
        downloads['epub'] = self.get_production_media_url(
            'epub',
            self.get_default_version(),
        )
        downloads['pdf'] = self.get_production_media_url(
            'pdf',
            self.get_default_version(),
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
        if settings.GLOBAL_PIP_CACHE and settings.DEBUG:
            return settings.GLOBAL_PIP_CACHE
        return os.path.join(self.doc_path, '.cache', 'pip')

    #
    # Paths for symlinks in project doc_path.
    #
    def translations_symlink_path(self, language=None):
        """Path in the doc_path that we symlink translations."""
        if not language:
            language = self.language
        return os.path.join(self.doc_path, 'translations', language)

    #
    # End symlink paths
    #

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
    def is_imported(self):
        return bool(self.repo)

    @property
    def has_good_build(self):
        # Check if there is `_good_build` annotation in the Queryset.
        # Used for Database optimization.
        if hasattr(self, '_good_build'):
            return self._good_build
        return self.builds.filter(success=True).exists()

    @property
    def has_versions(self):
        return self.versions.exists()

    @property
    def has_aliases(self):
        return self.aliases.exists()

    def has_media(self, type_, version_slug=LATEST):
        path = self.get_production_media_path(
            type_=type_, version_slug=version_slug
        )
        if os.path.exists(path):
            return True

        if settings.RTD_BUILD_MEDIA_STORAGE:
            storage = get_storage_class(settings.RTD_BUILD_MEDIA_STORAGE)()
            storage_path = self.get_storage_path(
                type_=type_, version_slug=version_slug
            )
            return storage.exists(storage_path)

        return False

    def has_pdf(self, version_slug=LATEST):
        return self.has_media(MEDIA_TYPE_PDF, version_slug=version_slug)

    def has_epub(self, version_slug=LATEST):
        return self.has_media(MEDIA_TYPE_EPUB, version_slug=version_slug)

    def has_htmlzip(self, version_slug=LATEST):
        return self.has_media(MEDIA_TYPE_HTMLZIP, version_slug=version_slug)

    @property
    def sponsored(self):
        return False

    def vcs_repo(self, version=LATEST, environment=None):
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

        backend = backend_cls.get(self.repo_type)
        if not backend:
            repo = None
        else:
            repo = backend(self, version, environment)
        return repo

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
                settings.DOCKER_LIMITS.get('time') or
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
        if hasattr(self, '_latest_build'):
            if self._latest_build:
                return self._latest_build[0]
            return None

        kwargs = {'type': 'html'}
        if finished:
            kwargs['state'] = 'finished'
        return self.builds.filter(**kwargs).first()

    def api_versions(self):
        from readthedocs.builds.models import APIVersion
        ret = []
        for version_data in api.project(self.pk
                                        ).active_versions.get()['versions']:
            version = APIVersion(**version_data)
            ret.append(version)
        return sort_version_aware(ret)

    def active_versions(self):
        from readthedocs.builds.models import Version
        versions = Version.objects.public(project=self, only_active=True)
        return (
            versions.filter(built=True, active=True) |
            versions.filter(active=True, uploaded=True)
        )

    def ordered_active_versions(self, user=None):
        from readthedocs.builds.models import Version
        kwargs = {
            'project': self,
            'only_active': True,
        }
        if user:
            kwargs['user'] = user
        versions = Version.objects.public(**kwargs).select_related(
            'project',
            'project__main_language_project',
        ).prefetch_related(
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
        return sort_version_aware(versions)

    def all_active_versions(self):
        """
        Get queryset with all active versions.

        .. note::
            This is a temporary workaround for activate_versions filtering out
            things that were active, but failed to build

        :returns: :py:class:`Version` queryset
        """
        return self.versions.filter(active=True)

    def get_stable_version(self):
        return self.versions.filter(slug=STABLE).first()

    def update_stable_version(self):
        """
        Returns the version that was promoted to be the new stable version.

        Return ``None`` if no update was made or if there is no version on the
        project that can be considered stable.
        """
        versions = self.versions.all()
        new_stable = determine_stable_version(versions)
        if new_stable:
            current_stable = self.get_stable_version()
            if current_stable:
                identifier_updated = (
                    new_stable.identifier != current_stable.identifier
                )
                if identifier_updated and current_stable.machine:
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
        return self.vcs_repo().fallback_branch

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
        """Get the parent project relationship or None if this is a top level project"""
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
        """Whether this project is ad-free (don't access the database)"""
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
        'Project',
        verbose_name=_('Project'),
        related_name='imported_files',
    )
    version = models.ForeignKey(
        'builds.Version',
        verbose_name=_('Version'),
        related_name='imported_files',
        null=True,
    )
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'))

    # max_length is set to 4096 because linux has a maximum path length
    # of 4096 characters for most filesystems (including EXT4).
    # https://github.com/rtfd/readthedocs.org/issues/5061
    path = models.CharField(_('Path'), max_length=4096)
    md5 = models.CharField(_('MD5 checksum'), max_length=255)
    commit = models.CharField(_('Commit'), max_length=255)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    def get_absolute_url(self):
        return resolve(
            project=self.project,
            version_slug=self.version.slug,
            filename=self.path,
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

    objects = HTMLFileManager()

    def get_processed_json(self):
        """
        Get the parsed JSON for search indexing.

        Check for two paths for each index file
        This is because HTMLDir can generate a file from two different places:

        * foo.rst
        * foo/index.rst

        Both lead to `foo/index.html`
        https://github.com/rtfd/readthedocs.org/issues/5368
        """
        paths = []
        basename = os.path.splitext(self.path)[0]
        paths.append(basename + '.fjson')
        if basename.endswith('/index'):
            new_basename = re.sub(r'\/index$', '', basename)
            paths.append(new_basename + '.fjson')

        full_json_path = self.project.get_production_media_path(
            type_='json', version_slug=self.version.slug, include_file=False
        )
        try:
            for path in paths:
                file_path = os.path.join(full_json_path, path)
                if os.path.exists(file_path):
                    return process_file(file_path)
        except Exception:
            log.warning(
                'Unhandled exception during search processing file: %s',
                file_path,
            )
        return {
            'headers': [],
            'content': '',
            'path': file_path,
            'title': '',
            'sections': [],
        }

    @cached_property
    def processed_json(self):
        return self.get_processed_json()


class Notification(models.Model):
    project = models.ForeignKey(Project, related_name='%(class)s_notifications')
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
        blank=True,
        help_text=_('URL to send the webhook to'),
    )

    def __str__(self):
        return self.url


class Domain(models.Model):

    """A custom domain name for a project."""

    project = models.ForeignKey(Project, related_name='domains')
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

    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        ordering = ('-canonical', '-machine', 'domain')

    def __str__(self):
        return '{domain} pointed at {project}'.format(
            domain=self.domain,
            project=self.project.name,
        )

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        from readthedocs.projects import tasks
        parsed = urlparse(self.domain)
        if parsed.scheme or parsed.netloc:
            self.domain = parsed.netloc
        else:
            self.domain = parsed.path
        super().save(*args, **kwargs)
        broadcast(
            type='app',
            task=tasks.symlink_domain,
            args=[self.project.pk, self.domain],
        )

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ
        from readthedocs.projects import tasks
        broadcast(
            type='app',
            task=tasks.symlink_domain,
            args=[self.project.pk, self.domain, True],
        )
        super().delete(*args, **kwargs)


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
    ALLOW_DEPRECATED_WEBHOOKS = 'allow_deprecated_webhooks'
    PIP_ALWAYS_UPGRADE = 'pip_always_upgrade'
    SKIP_SUBMODULES = 'skip_submodules'
    DONT_OVERWRITE_SPHINX_CONTEXT = 'dont_overwrite_sphinx_context'
    MKDOCS_THEME_RTD = 'mkdocs_theme_rtd'
    API_LARGE_DATA = 'api_large_data'
    DONT_SHALLOW_CLONE = 'dont_shallow_clone'
    USE_TESTING_BUILD_IMAGE = 'use_testing_build_image'
    SHARE_SPHINX_DOCTREE = 'share_sphinx_doctree'
    DEFAULT_TO_MKDOCS_0_17_3 = 'default_to_mkdocs_0_17_3'

    FEATURES = (
        (USE_SPHINX_LATEST, _('Use latest version of Sphinx')),
        (ALLOW_DEPRECATED_WEBHOOKS, _('Allow deprecated webhook views')),
        (PIP_ALWAYS_UPGRADE, _('Always run pip install --upgrade')),
        (SKIP_SUBMODULES, _('Skip git submodule checkout')),
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
            _('Install mkdocs 0.17.3 by default')
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        self.value = shlex_quote(self.value)
        return super().save(*args, **kwargs)
