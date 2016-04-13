"""Project models"""

import fnmatch
import logging
import sys
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from guardian.shortcuts import assign
from taggit.managers import TaggableManager

from readthedocs.api.client import api
from readthedocs.core.utils import broadcast
from readthedocs.restapi.client import api as apiv2
from readthedocs.builds.constants import LATEST, LATEST_VERBOSE_NAME, STABLE
from readthedocs.privacy.loader import (RelatedProjectManager, ProjectManager,
                                        ChildRelatedProjectManager)
from readthedocs.projects import constants
from readthedocs.projects.exceptions import ProjectImportError
from readthedocs.projects.templatetags.projects_tags import sort_version_aware
from readthedocs.projects.utils import make_api_version, update_static_metadata
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.projects.version_handling import version_windows
from readthedocs.core.resolver import resolve, resolve_domain
from readthedocs.core.validators import validate_domain_name

from readthedocs.vcs_support.base import VCSProject
from readthedocs.vcs_support.backends import backend_cls
from readthedocs.vcs_support.utils import Lock, NonBlockingLock

if sys.version_info > (3,):
    # pylint: disable=import-error
    from urllib.parse import urlparse
    # pylint: enable=import-error
else:
    from urlparse import urlparse

log = logging.getLogger(__name__)


class ProjectRelationship(models.Model):

    """Project to project relationship

    This is used for subprojects
    """

    parent = models.ForeignKey('Project', verbose_name=_('Parent'),
                               related_name='subprojects')
    child = models.ForeignKey('Project', verbose_name=_('Child'),
                              related_name='superprojects')
    alias = models.CharField(_('Alias'), max_length=255, null=True, blank=True)

    objects = ChildRelatedProjectManager()

    def __unicode__(self):
        return "%s -> %s" % (self.parent, self.child)

    def save(self, *args, **kwargs):
        if not self.alias:
            self.alias = self.child.slug
        super(ProjectRelationship, self).save(*args, **kwargs)

    # HACK
    def get_absolute_url(self):
        return resolve(self.child)


class Project(models.Model):

    """Project model"""

    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # Generally from conf.py
    users = models.ManyToManyField(User, verbose_name=_('User'),
                                   related_name='projects')
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True,
                                   help_text=_('The reStructuredText '
                                               'description of the project'))
    repo = models.CharField(_('Repository URL'), max_length=255,
                            help_text=_('Hosted documentation repository URL'))
    repo_type = models.CharField(_('Repository type'), max_length=10,
                                 choices=constants.REPO_CHOICES, default='git')
    project_url = models.URLField(_('Project homepage'), blank=True,
                                  help_text=_('The project\'s homepage'))
    canonical_url = models.URLField(_('Canonical URL'), blank=True,
                                    help_text=_('URL that documentation is expected to serve from'))
    version = models.CharField(_('Version'), max_length=100, blank=True,
                               help_text=_('Project version these docs apply '
                                           'to, i.e. 1.0a'))
    copyright = models.CharField(_('Copyright'), max_length=255, blank=True,
                                 help_text=_('Project copyright information'))
    theme = models.CharField(
        _('Theme'), max_length=20, choices=constants.DEFAULT_THEME_CHOICES,
        default=constants.THEME_DEFAULT,
        help_text=(u'<a href="http://sphinx.pocoo.org/theming.html#builtin-'
                   'themes" target="_blank">%s</a>') % _('Examples'))
    suffix = models.CharField(_('Suffix'), max_length=10, editable=False,
                              default='.rst')
    single_version = models.BooleanField(
        _('Single version'), default=False,
        help_text=_('A single version site has no translations and only your '
                    '"latest" version, served at the root of the domain. Use '
                    'this with caution, only turn it on if you will <b>never</b> '
                    'have multiple versions of your docs.'))
    default_version = models.CharField(
        _('Default version'), max_length=255, default=LATEST,
        help_text=_('The version of your project that / redirects to'))
    # In default_branch, None max_lengtheans the backend should choose the
    # appropraite branch. Eg 'master' for git
    default_branch = models.CharField(
        _('Default branch'), max_length=255, default=None, null=True,
        blank=True, help_text=_('What branch "latest" points to. Leave empty '
                                'to use the default value for your VCS (eg. '
                                '<code>trunk</code> or <code>master</code>).'))
    requirements_file = models.CharField(
        _('Requirements file'), max_length=255, default=None, null=True,
        blank=True, help_text=_(
            'A <a '
            'href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">'
            'pip requirements file</a> needed to build your documentation. '
            'Path from the root of your project.'))
    documentation_type = models.CharField(
        _('Documentation type'), max_length=20,
        choices=constants.DOCUMENTATION_CHOICES, default='sphinx',
        help_text=_('Type of documentation you are building. <a href="http://'
                    'sphinx-doc.org/builders.html#sphinx.builders.html.'
                    'DirectoryHTMLBuilder">More info</a>.'))

    # Project features
    allow_comments = models.BooleanField(_('Allow Comments'), default=False)
    comment_moderation = models.BooleanField(_('Comment Moderation)'), default=False)
    cdn_enabled = models.BooleanField(_('CDN Enabled'), default=False)
    analytics_code = models.CharField(
        _('Analytics code'), max_length=50, null=True, blank=True,
        help_text=_("Google Analytics Tracking ID "
                    "(ex. <code>UA-22345342-1</code>). "
                    "This may slow down your page loads."))
    container_image = models.CharField(
        _('Alternative container image'), max_length=64, null=True, blank=True)
    container_mem_limit = models.CharField(
        _('Container memory limit'), max_length=10, null=True, blank=True,
        help_text=_("Memory limit in Docker format "
                    "-- example: <code>512m</code> or <code>1g</code>"))
    container_time_limit = models.CharField(
        _('Container time limit'), max_length=10, null=True, blank=True)
    build_queue = models.CharField(
        _('Alternate build queue id'), max_length=32, null=True, blank=True)
    allow_promos = models.BooleanField(
        _('Sponsor advertisements'), default=True, help_text=_(
            "Allow sponsor advertisements on my project documentation"))

    # Sphinx specific build options.
    enable_epub_build = models.BooleanField(
        _('Enable EPUB build'), default=True,
        help_text=_(
            'Create a EPUB version of your documentation with each build.'))
    enable_pdf_build = models.BooleanField(
        _('Enable PDF build'), default=True,
        help_text=_(
            'Create a PDF version of your documentation with each build.'))

    # Other model data.
    path = models.CharField(_('Path'), max_length=255, editable=False,
                            help_text=_("The directory where "
                                        "<code>conf.py</code> lives"))
    conf_py_file = models.CharField(
        _('Python configuration file'), max_length=255, default='', blank=True,
        help_text=_('Path from project root to <code>conf.py</code> file '
                    '(ex. <code>docs/conf.py</code>).'
                    'Leave blank if you want us to find it for you.'))

    featured = models.BooleanField(_('Featured'), default=False)
    skip = models.BooleanField(_('Skip'), default=False)
    mirror = models.BooleanField(_('Mirror'), default=False)
    install_project = models.BooleanField(
        _('Install Project'),
        help_text=_("Install your project inside a virtualenv using <code>setup.py "
                    "install</code>"),
        default=False
    )

    # This model attribute holds the python interpreter used to create the
    # virtual environment
    python_interpreter = models.CharField(
        _('Python Interpreter'),
        max_length=20,
        choices=constants.PYTHON_CHOICES,
        default='python',
        help_text=_("(Beta) The Python interpreter used to create the virtual "
                    "environment."))

    use_system_packages = models.BooleanField(
        _('Use system packages'),
        help_text=_("Give the virtual environment access to the global "
                    "site-packages dir."),
        default=False
    )
    django_packages_url = models.CharField(_('Django Packages URL'),
                                           max_length=255, blank=True)
    privacy_level = models.CharField(
        _('Privacy Level'), max_length=20, choices=constants.PRIVACY_CHOICES,
        default=getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public'),
        help_text=_("(Beta) Level of privacy that you want on the repository. "
                    "Protected means public but not in listings."))
    version_privacy_level = models.CharField(
        _('Version Privacy Level'), max_length=20,
        choices=constants.PRIVACY_CHOICES, default=getattr(
            settings, 'DEFAULT_PRIVACY_LEVEL', 'public'),
        help_text=_("(Beta) Default level of privacy you want on built "
                    "versions of documentation."))

    # Subprojects
    related_projects = models.ManyToManyField(
        'self', verbose_name=_('Related projects'), blank=True,
        symmetrical=False, through=ProjectRelationship)

    # Language bits
    language = models.CharField(_('Language'), max_length=20, default='en',
                                help_text=_("The language the project "
                                            "documentation is rendered in. "
                                            "Note: this affects your project's URL."),
                                choices=constants.LANGUAGES)

    programming_language = models.CharField(
        _('Programming Language'),
        max_length=20,
        default='words',
        help_text=_("The primary programming language the project is written in."),
        choices=constants.PROGRAMMING_LANGUAGES, blank=True)
    # A subproject pointed at it's main language, so it can be tracked
    main_language_project = models.ForeignKey('self',
                                              related_name='translations',
                                              blank=True, null=True)

    # Version State
    num_major = models.IntegerField(
        _('Number of Major versions'),
        default=2,
        null=True,
        blank=True,
        help_text=_("2 means supporting 3.X.X and 2.X.X, but not 1.X.X")
    )
    num_minor = models.IntegerField(
        _('Number of Minor versions'),
        default=2,
        null=True,
        blank=True,
        help_text=_("2 means supporting 2.2.X and 2.1.X, but not 2.0.X")
    )
    num_point = models.IntegerField(
        _('Number of Point versions'),
        default=2,
        null=True,
        blank=True,
        help_text=_("2 means supporting 2.2.2 and 2.2.1, but not 2.2.0")
    )

    has_valid_webhook = models.BooleanField(
        default=False, help_text=_('This project has been built with a webhook')
    )
    has_valid_clone = models.BooleanField(
        default=False, help_text=_('This project has been successfully cloned')
    )

    tags = TaggableManager(blank=True)
    objects = ProjectManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ('slug',)
        permissions = (
            # Translators: Permission around whether a user can view the
            # project
            ('view_project', _('View Project')),
        )

    def __unicode__(self):
        return self.name

    def sync_supported_versions(self):
        supported = self.supported_versions()
        if supported:
            self.versions.filter(
                verbose_name__in=supported).update(supported=True)
            self.versions.exclude(
                verbose_name__in=supported).update(supported=False)
            self.versions.filter(verbose_name=LATEST_VERBOSE_NAME).update(supported=True)

    def save(self, *args, **kwargs):
        from readthedocs.projects import tasks
        first_save = self.pk is None
        if not self.slug:
            # Subdomains can't have underscores in them.
            self.slug = slugify(self.name).replace('_', '-')
            if self.slug == '':
                raise Exception(_("Model must have slug"))
        super(Project, self).save(*args, **kwargs)
        for owner in self.users.all():
            assign('view_project', owner, self)
        try:
            if self.default_branch:
                latest = self.versions.get(slug=LATEST)
                if latest.identifier != self.default_branch:
                    latest.identifier = self.default_branch
                    latest.save()
        except Exception:
            log.error('Failed to update latest identifier', exc_info=True)

        # Add exceptions here for safety
        try:
            self.sync_supported_versions()
        except Exception:
            log.error('failed to sync supported versions', exc_info=True)
        try:
            if not first_save:
                broadcast(type='app', task=tasks.symlink_project, args=[self.pk])
        except Exception:
            log.error('failed to symlink project', exc_info=True)
        try:
            update_static_metadata(project_pk=self.pk)
        except Exception:
            log.error('failed to update static metadata', exc_info=True)
        try:
            branch = self.default_branch or self.vcs_repo().fallback_branch
            if not self.versions.filter(slug=LATEST).exists():
                self.versions.create_latest(identifier=branch)
        except Exception:
            log.error('Error creating default branches', exc_info=True)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None, lang_slug=None, private=None):
        """Return a url for the docs

        Always use http for now, to avoid content warnings.
        """
        return resolve(project=self, version_slug=version_slug, language=lang_slug, private=private)

    def get_builds_url(self):
        return reverse('builds_project_list', kwargs={
            'project_slug': self.slug,
        })

    def get_canonical_url(self):
        if getattr(settings, 'DONT_HIT_DB', True):
            return apiv2.project(self.pk).canonical_url().get()['url']
        else:
            return self.get_docs_url()

    def get_subproject_urls(self):
        """List subproject URLs

        This is used in search result linking
        """
        if getattr(settings, 'DONT_HIT_DB', True):
            return [(proj['slug'], proj['canonical_url'])
                    for proj in (
                        apiv2.project(self.pk)
                        .subprojects()
                        .get()['subprojects'])]
        else:
            return [(proj.child.slug, proj.child.get_docs_url())
                    for proj in self.subprojects.all()]

    def get_production_media_path(self, type_, version_slug, include_file=True):
        """
        This is used to see if these files exist so we can offer them for download.

        :param type_: Media content type, ie - 'pdf', 'zip'
        :param version_slug: Project version slug for lookup
        :param include_file: Include file name in return
        :type include_file: bool
        :returns: Full path to media file or path
        """
        if getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public') == 'public' or settings.DEBUG:
            path = os.path.join(
                settings.MEDIA_ROOT, type_, self.slug, version_slug)
        else:
            path = os.path.join(
                settings.PRODUCTION_MEDIA_ARTIFACTS, type_, self.slug, version_slug)
        if include_file:
            path = os.path.join(
                path, '%s.%s' % (self.slug, type_.replace('htmlzip', 'zip')))
        return path

    def get_production_media_url(self, type_, version_slug, full_path=True):
        """Get the URL for downloading a specific media file."""
        path = reverse('project_download_media', kwargs={
            'project_slug': self.slug,
            'type_': type_,
            'version_slug': version_slug,
        })
        if full_path:
            path = '//%s%s' % (settings.PRODUCTION_DOMAIN, path)
        return path

    def subdomain(self):
        """Get project subdomain from resolver"""
        return resolve_domain(self)

    def get_downloads(self):
        downloads = {}
        downloads['htmlzip'] = self.get_production_media_url(
            'htmlzip', self.get_default_version())
        downloads['epub'] = self.get_production_media_url(
            'epub', self.get_default_version())
        downloads['pdf'] = self.get_production_media_url(
            'pdf', self.get_default_version())
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
        """Path to pip cache"""
        return os.path.join(self.doc_path, '.cache', 'pip')

    #
    # Paths for symlinks in project doc_path.
    #
    def translations_symlink_path(self, language=None):
        """Path in the doc_path that we symlink translations"""
        if not language:
            language = self.language
        return os.path.join(self.doc_path, 'translations', language)

    #
    # End symlink paths
    #

    def full_doc_path(self, version=LATEST):
        """The path to the documentation root in the project"""
        doc_base = self.checkout_path(version)
        for possible_path in ['docs', 'doc', 'Doc']:
            if os.path.exists(os.path.join(doc_base, '%s' % possible_path)):
                return os.path.join(doc_base, '%s' % possible_path)
        # No docs directory, docs are at top-level.
        return doc_base

    def artifact_path(self, type_, version=LATEST):
        """The path to the build html docs in the project"""
        return os.path.join(self.doc_path, "artifacts", version, type_)

    def full_build_path(self, version=LATEST):
        """The path to the build html docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "html")

    def full_latex_path(self, version=LATEST):
        """The path to the build LaTeX docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "latex")

    def full_epub_path(self, version=LATEST):
        """The path to the build epub docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "epub")

    # There is currently no support for building man/dash formats, but we keep
    # the support there for existing projects. They might have already existing
    # legacy builds.

    def full_man_path(self, version=LATEST):
        """The path to the build man docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "man")

    def full_dash_path(self, version=LATEST):
        """The path to the build dash docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "dash")

    def full_json_path(self, version=LATEST):
        """The path to the build json docs in the project"""
        if 'sphinx' in self.documentation_type:
            return os.path.join(self.conf_dir(version), "_build", "json")
        elif 'mkdocs' in self.documentation_type:
            return os.path.join(self.checkout_path(version), "_build", "json")

    def full_singlehtml_path(self, version=LATEST):
        """The path to the build singlehtml docs in the project"""
        return os.path.join(self.conf_dir(version), "_build", "singlehtml")

    def rtd_build_path(self, version=LATEST):
        """The destination path where the built docs are copied"""
        return os.path.join(self.doc_path, 'rtd-builds', version)

    def static_metadata_path(self):
        """The path to the static metadata JSON settings file"""
        return os.path.join(self.doc_path, 'metadata.json')

    def conf_file(self, version=LATEST):
        """Find a ``conf.py`` file in the project checkout"""
        if self.conf_py_file:
            conf_path = os.path.join(self.checkout_path(version), self.conf_py_file)
            if os.path.exists(conf_path):
                log.info('Inserting conf.py file path from model')
                return conf_path
            else:
                log.warning("Conf file specified on model doesn't exist")
        files = self.find('conf.py', version)
        if not files:
            files = self.full_find('conf.py', version)
        if len(files) == 1:
            return files[0]
        for filename in files:
            if filename.find('doc', 70) != -1:
                return filename
        # Having this be translatable causes this odd error:
        # ProjectImportError(<django.utils.functional.__proxy__ object at
        # 0x1090cded0>,)
        raise ProjectImportError(
            u"Conf File Missing. Please make sure you have a conf.py in your project.")

    def conf_dir(self, version=LATEST):
        conf_file = self.conf_file(version)
        if conf_file:
            return os.path.dirname(conf_file)

    @property
    def is_type_sphinx(self):
        """Is project type Sphinx"""
        return 'sphinx' in self.documentation_type

    @property
    def is_type_mkdocs(self):
        """Is project type Mkdocs"""
        return 'mkdocs' in self.documentation_type

    @property
    def is_imported(self):
        return bool(self.repo)

    @property
    def has_good_build(self):
        return self.builds.filter(success=True).exists()

    @property
    def has_versions(self):
        return self.versions.exists()

    @property
    def has_aliases(self):
        return self.aliases.exists()

    def has_pdf(self, version_slug=LATEST):
        if not self.enable_pdf_build:
            return False
        return os.path.exists(self.get_production_media_path(
            type_='pdf', version_slug=version_slug))

    def has_epub(self, version_slug=LATEST):
        if not self.enable_epub_build:
            return False
        return os.path.exists(self.get_production_media_path(
            type_='epub', version_slug=version_slug))

    def has_htmlzip(self, version_slug=LATEST):
        return os.path.exists(self.get_production_media_path(
            type_='htmlzip', version_slug=version_slug))

    @property
    def sponsored(self):
        return False

    def vcs_repo(self, version=LATEST):
        backend = backend_cls.get(self.repo_type)
        if not backend:
            repo = None
        else:
            proj = VCSProject(
                self.name, self.default_branch, self.checkout_path(version), self.clean_repo)
            repo = backend(proj, version)
        return repo

    def repo_nonblockinglock(self, version, max_lock_age=5):
        return NonBlockingLock(project=self, version=version, max_lock_age=max_lock_age)

    def repo_lock(self, version, timeout=5, polling_interval=5):
        return Lock(self, version, timeout, polling_interval)

    def find(self, filename, version):
        """Find files inside the project's ``doc`` path

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.full_doc_path(version)):
            for filename in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, filename))
        return matches

    def full_find(self, filename, version):
        """Find files inside a project's checkout path

        :param filename: Filename to search for in project checkout
        :param version: Version instance to set version checkout path
        """
        matches = []
        for root, __, filenames in os.walk(self.checkout_path(version)):
            for filename in fnmatch.filter(filenames, filename):
                matches.append(os.path.join(root, filename))
        return matches

    def get_latest_build(self, finished=True):
        """
        Get latest build for project

        finished
            Return only builds that are in a finished state
        """
        kwargs = {'type': 'html'}
        if finished:
            kwargs['state'] = 'finished'
        return self.builds.filter(**kwargs).first()

    def api_versions(self):
        ret = []
        for version_data in api.version.get(project=self.pk,
                                            active=True)['objects']:
            version = make_api_version(version_data)
            ret.append(version)
        return sort_version_aware(ret)

    def active_versions(self):
        from readthedocs.builds.models import Version
        versions = Version.objects.public(project=self, only_active=True)
        return (versions.filter(built=True, active=True) |
                versions.filter(active=True, uploaded=True))

    def ordered_active_versions(self, user=None):
        from readthedocs.builds.models import Version
        kwargs = {
            'project': self,
            'only_active': True,
        }
        if user:
            kwargs['user'] = user
        versions = Version.objects.public(**kwargs)
        return sort_version_aware(versions)

    def all_active_versions(self):
        """Get queryset with all active versions

        .. note::
            This is a temporary workaround for activate_versions filtering out
            things that were active, but failed to build

        :returns: :py:cls:`Version` queryset
        """
        return self.versions.filter(active=True)

    def supported_versions(self):
        """Get the list of supported versions

        :returns: List of version strings.
        """
        if not self.num_major or not self.num_minor or not self.num_point:
            return []
        version_identifiers = self.versions.values_list('verbose_name', flat=True)
        return version_windows(
            version_identifiers,
            major=self.num_major,
            minor=self.num_minor,
            point=self.num_point,
        )

    def get_stable_version(self):
        return self.versions.filter(slug=STABLE).first()

    def update_stable_version(self):
        """Returns the version that was promoted to be the new stable version

        Return ``None`` if no update was mode or if there is no version on the
        project that can be considered stable.
        """
        versions = self.versions.all()
        new_stable = determine_stable_version(versions)
        if new_stable:
            current_stable = self.get_stable_version()
            if current_stable:
                identifier_updated = (
                    new_stable.identifier != current_stable.identifier)
                if identifier_updated and current_stable.machine:
                    log.info(
                        "Update stable version: {project}:{version}".format(
                            project=self.slug,
                            version=new_stable.identifier))
                    current_stable.identifier = new_stable.identifier
                    current_stable.save()
                    return new_stable
            else:
                log.info(
                    "Creating new stable version: {project}:{version}".format(
                        project=self.slug,
                        version=new_stable.identifier))
                current_stable = self.versions.create_stable(
                    type=new_stable.type,
                    identifier=new_stable.identifier)
                return new_stable

    def versions_from_branch_name(self, branch):
        return (
            self.versions.filter(identifier=branch) |
            self.versions.filter(identifier='remotes/origin/%s' % branch) |
            self.versions.filter(identifier='origin/%s' % branch)
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
            slug=self.default_version, active=True
        )
        if version_qs.exists():
            return self.default_version
        return LATEST

    def get_default_branch(self):
        """Get the version representing 'latest'"""
        if self.default_branch:
            return self.default_branch
        else:
            return self.vcs_repo().fallback_branch

    def add_subproject(self, child, alias=None):
        subproject, __ = ProjectRelationship.objects.get_or_create(
            parent=self, child=child, alias=alias,
        )
        return subproject

    def remove_subproject(self, child):
        ProjectRelationship.objects.filter(parent=self, child=child).delete()
        return

    def moderation_queue(self):
        # non-optimal SQL warning.
        from readthedocs.comments.models import DocumentComment
        queue = []
        comments = DocumentComment.objects.filter(node__project=self)
        for comment in comments:
            if not comment.has_been_approved_since_most_recent_node_change():
                queue.append(comment)

        return queue

    def add_node(self, content_hash, page, version, commit):
        """Add comment node

        :param content_hash: Hash of node content
        :param page: Doc page for node
        :param version: Slug for project version to apply node to
        :type version: str
        :param commit: Commit that node was updated in
        :type commit: str
        """
        from readthedocs.comments.models import NodeSnapshot, DocumentNode
        project_obj = Project.objects.get(slug=self.slug)
        version_obj = project_obj.versions.get(slug=version)
        try:
            NodeSnapshot.objects.get(hash=content_hash, node__project=project_obj,
                                     node__version=version_obj, node__page=page,
                                     commit=commit)
            return False  # ie, no new node was created.
        except NodeSnapshot.DoesNotExist:
            DocumentNode.objects.create(
                hash=content_hash,
                page=page,
                project=project_obj,
                version=version_obj,
                commit=commit
            )
        return True  # ie, it's True that a new node was created.

    def add_comment(self, version_slug, page, content_hash, commit, user, text):
        """Add comment to node

        :param version_slug: Version slug to use for node lookup
        :param page: Page to attach comment to
        :param content_hash: Hash of content to apply comment to
        :param commit: Commit that updated comment
        :param user: :py:cls:`User` instance that created comment
        :param text: Comment text
        """
        from readthedocs.comments.models import DocumentNode
        try:
            node = self.nodes.from_hash(version_slug, page, content_hash)
        except DocumentNode.DoesNotExist:
            version = self.versions.get(slug=version_slug)
            node = self.nodes.create(version=version, page=page,
                                     hash=content_hash, commit=commit)
        return node.comments.create(user=user, text=text)


class ImportedFile(models.Model):

    """Imported files model

    This tracks files that are output from documentation builds, useful for
    things like CDN invalidation.
    """

    project = models.ForeignKey('Project', verbose_name=_('Project'),
                                related_name='imported_files')
    version = models.ForeignKey('builds.Version', verbose_name=_('Version'),
                                related_name='imported_files', null=True)
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'))
    path = models.CharField(_('Path'), max_length=255)
    md5 = models.CharField(_('MD5 checksum'), max_length=255)
    commit = models.CharField(_('Commit'), max_length=255)

    @models.permalink
    def get_absolute_url(self):
        return ('docs_detail', [self.project.slug, self.project.language,
                                self.version.slug, self.path])

    def __unicode__(self):
        return '%s: %s' % (self.name, self.project)


class Notification(models.Model):
    project = models.ForeignKey(Project,
                                related_name='%(class)s_notifications')
    objects = RelatedProjectManager()

    class Meta:
        abstract = True


class EmailHook(Notification):
    email = models.EmailField()

    def __unicode__(self):
        return self.email


class WebHook(Notification):
    url = models.URLField(blank=True,
                          help_text=_('URL to send the webhook to'))

    def __unicode__(self):
        return self.url


class Domain(models.Model):
    project = models.ForeignKey(Project, related_name='domains')
    domain = models.CharField(_('Domain'), unique=True, max_length=255,
                              validators=[validate_domain_name])
    machine = models.BooleanField(
        default=False, help_text=_('This Domain was auto-created')
    )
    cname = models.BooleanField(
        default=False, help_text=_('This Domain is a CNAME for the project')
    )
    canonical = models.BooleanField(
        default=False,
        help_text=_('This Domain is the primary one where the documentation is served from.')
    )
    count = models.IntegerField(default=0, help_text=_('Number of times this domain has been hit.'))

    objects = RelatedProjectManager()

    class Meta:
        ordering = ('-canonical', '-machine', 'domain')

    def __unicode__(self):
        return "{domain} pointed at {project}".format(domain=self.domain, project=self.project.name)

    def save(self, *args, **kwargs):
        from readthedocs.projects import tasks
        parsed = urlparse(self.domain)
        if parsed.scheme or parsed.netloc:
            self.domain = parsed.netloc
        else:
            self.domain = parsed.path
        super(Domain, self).save(*args, **kwargs)
        broadcast(type='app', task=tasks.symlink_domain, args=[self.project.pk, self.pk])

    def delete(self, *args, **kwargs):
        from readthedocs.projects import tasks
        broadcast(type='app', task=tasks.symlink_domain, args=[self.project.pk, self.pk, True])
        super(Domain, self).delete(*args, **kwargs)
