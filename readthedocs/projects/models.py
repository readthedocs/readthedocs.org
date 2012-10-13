import fnmatch
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from projects import constants
from projects.exceptions import ProjectImportError
from projects.templatetags.projects_tags import sort_version_aware
from projects.utils import diff, dmp, safe_write
from projects.utils import highest_version as _highest
from taggit.managers import TaggableManager
from tastyapi.slum import api

from vcs_support.base import VCSProject
from vcs_support.backends import backend_cls
from vcs_support.utils import Lock


log = logging.getLogger(__name__)

class ProjectManager(models.Manager):
    def live(self, *args, **kwargs):
        base_qs = self.filter(skip=False)
        return base_qs.filter(*args, **kwargs)

class ProjectRelationship(models.Model):
    parent = models.ForeignKey('Project', verbose_name=_('Parent'), related_name='subprojects')
    child = models.ForeignKey('Project', verbose_name=_('Child'), related_name='superprojects')

    def __unicode__(self):
        return "%s -> %s" % (self.parent, self.child)

    #HACK
    def get_absolute_url(self):
        return "http://%s.readthedocs.org/projects/%s/en/latest/" % (self.parent.slug, self.child.slug)

class Project(models.Model):
    #Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    #Generally from conf.py
    users = models.ManyToManyField(User, verbose_name=_('User'), related_name='projects')
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=True,
        help_text=_('The reStructuredText description of the project'))
    repo = models.CharField(_('Repository URL'), max_length=100, blank=True,
            help_text=_('Checkout URL for your code (hg, git, etc.). Ex. http://github.com/ericholscher/django-kong.git'))
    repo_type = models.CharField(_('Repository type'), max_length=10, choices=constants.REPO_CHOICES, default='git')
    project_url = models.URLField(_('Project URL'), blank=True, help_text=_('The project\'s homepage'), verify_exists=False)
    version = models.CharField(_('Version'), max_length=100, blank=True,
        help_text=_('Project version these docs apply to, i.e. 1.0a'))
    copyright = models.CharField(_('Copyright'), max_length=255, blank=True,
        help_text=_('Project copyright information'))
    theme = models.CharField(_('Theme'), max_length=20,
        choices=constants.DEFAULT_THEME_CHOICES, default=constants.THEME_DEFAULT,
        help_text=u'<a href="http://sphinx.pocoo.org/theming.html#builtin-themes" target="_blank">%s</a>' % _('Examples'))
    suffix = models.CharField(_('Suffix'), max_length=10, editable=False, default='.rst')
    default_version = models.CharField(_('Default version'), max_length=255, default='latest', help_text=_('The version of your project that / redirects to'))
    # In default_branch, None max_lengtheans the backend should choose the appropraite branch. Eg 'master' for git
    default_branch = models.CharField(_('Default branch'), max_length=255, default=None, null=True,
        blank=True, help_text=_('What branch "latest" points to. Leave empty to use the default value for your VCS (eg. trunk or master).'))
    requirements_file = models.CharField(_('Requirements file'), max_length=255, default=None, null=True, blank=True, help_text=_('Requires Virtualenv. A pip requirements file needed to build your documentation. Path from the root of your project.'))
    documentation_type = models.CharField(_('Documentation type'), max_length=20,
        choices=constants.DOCUMENTATION_CHOICES, default='sphinx',
        help_text=_('Type of documentation you are building. <a href="http://sphinx.pocoo.org/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info</a>.'))
    analytics_code = models.CharField(_('Analytics code'), max_length=50, null=True, blank=True, help_text=_("Google Analytics Tracking ID (ex. UA-22345342-1). This may slow down your page loads."))

    #Other model data.
    path = models.CharField(_('Path'), help_text=_("The directory where conf.py lives"),
                            max_length=255, editable=False)
    conf_py_file = models.CharField(_('Python configuration file'),
        help_text=_("Path from project root to conf.py file (ex. docs/conf.py). Leave blank if you want us to find it for you."),
        max_length=255, default='', blank=True)
    featured = models.BooleanField(_('Featured'))
    skip = models.BooleanField(_('Skip'))
    use_virtualenv = models.BooleanField(_('Use virtualenv'),
        help_text=_("Install your project inside a virtualenv using setup.py install"))
    use_system_packages = models.BooleanField(_('Use system packages'),
        help_text=_("Give the virtual environment access to the global sites-packages dir"))
    django_packages_url = models.CharField(_('Django Packages URL'), max_length=255, blank=True)
    crate_url = models.CharField(_('Crate URL'), max_length=255, blank=True)

    #Subprojects
    related_projects = models.ManyToManyField('self', verbose_name=_('Related projects'), blank=True, null=True, symmetrical=False, through=ProjectRelationship)

    tags = TaggableManager(blank=True)
    objects = ProjectManager()

    class Meta:
        ordering = ('slug',)

    def __unicode__(self):
        return self.name

    @property
    def subdomain(self):
        prod_domain = getattr(settings, 'PRODUCTION_DOMAIN')
        subdomain_slug = self.slug.replace('_', '-')
        return "%s.%s" % (subdomain_slug, prod_domain)

    def save(self, *args, **kwargs):
        #if hasattr(self, 'pk'):
            #previous_obj = self.__class__.objects.get(pk=self.pk)
            #if previous_obj.repo != self.repo:
                #Needed to not have an import loop on Project
                #from projects import tasks
                #This needs to run on the build machine.
                #tasks.remove_dir.delay(os.path.join(self.doc_path, 'checkouts'))
        if not self.slug:
            self.slug = slugify(self.name)
            if self.slug == '':
                raise Exception(_("Model must have slug"))
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None):
        """
        Return a url for the docs. Always use http for now,
        to avoid content warnings.
        """
        protocol = "http"
        version = version_slug or self.get_default_version()
        use_subdomain = getattr(settings, 'USE_SUBDOMAIN', False)
        if use_subdomain:
            return "%s://%s/%s/%s/" % (
                protocol,
                self.subdomain,
                'en',
                version,
            )
        else:
            return reverse('docs_detail', kwargs={
                'project_slug': self.slug,
                'lang_slug': 'en',
                'version_slug': version,
                'filename': ''
            })



    def get_builds_url(self):
        return reverse('builds_project_list', kwargs={
            'project_slug': self.slug,
        })

    def get_pdf_url(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_URL,
                                'pdf',
                                self.slug,
                                version_slug,
                                '%s.pdf' % self.slug)
        return path

    def get_pdf_path(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_ROOT,
                                'pdf',
                                self.slug,
                                version_slug,
                                '%s.pdf' % self.slug)
        return path

    def get_epub_url(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_URL,
                                'epub',
                                self.slug,
                                version_slug,
                                '%s.epub' % self.slug)
        return path

    def get_epub_path(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_ROOT,
                                'epub',
                                self.slug,
                                version_slug,
                                '%s.epub' % self.slug)
        return path

    def get_manpage_url(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_URL,
                                'man',
                                self.slug,
                                version_slug,
                                '%s.1' % self.slug)
        return path

    def get_manpage_path(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_ROOT,
                                'man',
                                self.slug,
                                version_slug,
                                '%s.1' % self.slug)
        return path

    def get_htmlzip_url(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_URL,
                                'htmlzip',
                                self.slug,
                                version_slug,
                                '%s.zip' % self.slug)
        return path

    def get_htmlzip_path(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_ROOT,
                                'htmlzip',
                                self.slug,
                                version_slug,
                                '%s.zip' % self.slug)
        return path

    #Doc PATH:
    #MEDIA_ROOT/slug/checkouts/version/<repo>

    @property
    def doc_path(self):
        return os.path.join(settings.DOCROOT, self.slug)

    def checkout_path(self, version='latest'):
        return os.path.join(self.doc_path, 'checkouts', version)

    def venv_path(self, version='latest'):
        return os.path.join(self.doc_path, 'envs', version)

    def venv_bin(self, version='latest', bin='python'):
        return os.path.join(self.venv_path(version), 'bin', bin)

    def full_doc_path(self, version='latest'):
        """
        The path to the documentation root in the project.
        """
        doc_base = self.checkout_path(version)
        for possible_path in ['docs', 'doc', 'Doc']:
            if os.path.exists(os.path.join(doc_base, '%s' % possible_path)):
                return os.path.join(doc_base, '%s' % possible_path)
        #No docs directory, docs are at top-level.
        return doc_base

    def full_build_path(self, version='latest'):
        """
        The path to the build html docs in the project.
        """
        return os.path.join(self.conf_dir(version), "_build", "html")

    def full_latex_path(self, version='latest'):
        """
        The path to the build latex docs in the project.
        """
        return os.path.join(self.conf_dir(version), "_build", "latex")

    def rtd_build_path(self, version="latest"):
        """
        The path to the build html docs in the project.
        """
        return os.path.join(self.doc_path, 'rtd-builds', version)

    def rtd_cname_path(self, cname):
        """
        The path to the build html docs in the project.
        """
        return os.path.join(settings.CNAME_ROOT, cname)

    def conf_file(self, version='latest'):
        if self.conf_py_file:
            log.debug('Inserting conf.py file path from model')
            return os.path.join(self.checkout_path(version), self.conf_py_file)
        files = self.find('conf.py', version)
        if not files:
            files = self.full_find('conf.py', version)
        if len(files) == 1:
            return files[0]
        elif len(files) > 1:
            for file in files:
                if file.find('doc', 70) != -1:
                    return file
        else:
            raise ProjectImportError(_("Conf File Missing."))

    def conf_dir(self, version='latest'):
        conf_file = self.conf_file(version)
        if conf_file:
            return conf_file.replace('/conf.py', '')

    @property
    def highest_version(self):
        return _highest(self.api_versions())

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

    def has_pdf(self, version_slug='latest'):
        return os.path.exists(self.get_pdf_path(version_slug))

    def has_manpage(self, version_slug='latest'):
        return os.path.exists(self.get_manpage_path(version_slug))

    def has_epub(self, version_slug='latest'):
        return os.path.exists(self.get_epub_path(version_slug))

    def has_htmlzip(self, version_slug='latest'):
        return os.path.exists(self.get_htmlzip_path(version_slug))

    @property
    def sponsored(self):
        return False

    def vcs_repo(self, version='latest'):
        #if hasattr(self, '_vcs_repo'):
            #return self._vcs_repo
        backend = backend_cls.get(self.repo_type)
        if not backend:
            repo = None
        else:
            proj = VCSProject(self.name,
                              self.default_branch,
                              self.checkout_path(version),
                              self.repo)
            repo = backend(proj, version)
        #self._vcs_repo = repo
        return repo

    @property
    def contribution_backend(self):
        if hasattr(self, '_contribution_backend'):
            return self._contribution_backend
        if not self.vcs_repo:
            cb = None
        else:
            cb = self.vcs_repo.get_contribution_backend()
        self._contribution_backend = cb
        return cb

    def repo_lock(self, timeout=5, polling_interval=0.2):
        return Lock(self, timeout, polling_interval)

    def find(self, file, version):
        """
        A balla API to find files inside of a projects dir.
        """
        matches = []
        for root, dirnames, filenames in os.walk(self.full_doc_path(version)):
            for filename in fnmatch.filter(filenames, file):
                matches.append(os.path.join(root, filename))
        return matches

    def full_find(self, file, version):
        """
        A balla API to find files inside of a projects dir.
        """
        matches = []
        for root, dirnames, filenames in os.walk(self.checkout_path(version)):
            for filename in fnmatch.filter(filenames, file):
                matches.append(os.path.join(root, filename))
        return matches

    def get_latest_build(self):
        try:
            return self.builds.filter(type='html')[0]
        except IndexError:
            return None

    def api_versions(self):
        from builds.models import Version
        ret = []
        for version_data in api.version.get(project=self.pk, active=True)['objects']:
            del version_data['resource_uri']
            project_data = version_data['project']
            del project_data['users']
            del project_data['resource_uri']
            del project_data['absolute_url']
            project = Project(**project_data)
            version_data['project'] = project
            ret.append(Version(**version_data))
        return sort_version_aware(ret)

    def active_versions(self):
        return (self.versions.filter(built=True, active=True) |
                self.versions.filter(active=True, uploaded=True))

    def ordered_active_versions(self):
        return sort_version_aware(self.versions.filter(active=True))


    def all_active_versions(self):
        "A temporary workaround for active_versions filtering out things that were active, but failed to build"
        return self.versions.filter(active=True)

    def version_from_branch_name(self, branch):
        try:
            return (self.versions.filter(identifier=branch) |
                    self.versions.filter(identifier='remotes/origin/%s'%branch))[0]
        except IndexError:
            return None


    @property
    def whitelisted(self):
        #Hack this true for now.
        return True

    #File Building stuff.
    #Not sure if this is used
    def get_top_level_files(self):
        return self.files.live(parent__isnull=True).order_by('ordering')

    def get_index_filename(self):
        return os.path.join(self.path, 'index.rst')

    def get_rendered_index(self):
        return render_to_string('projects/index.rst.html', {'project': self})

    def write_index(self):
        if not self.is_imported:
            safe_write(self.get_index_filename(), self.get_rendered_index())

    def get_latest_revisions(self):
        revision_qs = FileRevision.objects.filter(file__project=self,
            file__status=constants.LIVE_STATUS)
        return revision_qs.order_by('-created_date')

    def get_default_version(self):
        """
        Get the default version (slug).

        Returns self.default_version if the version with that slug actually
        exists (is built and published). Otherwise returns 'latest'.
        """
        # latest is a special case where we don't have to check if it exists
        if self.default_version == 'latest':
            return self.default_version
        # check if the default_version exists
        version_qs = self.versions.filter(
            slug=self.default_version,
            active=True
        )
        if version_qs.exists():
            return self.default_version
        return 'latest'

    def add_subproject(self, child):
        subproject, created = ProjectRelationship.objects.get_or_create(
            parent=self,
            child=child,
            )
        return subproject

    def remove_subproject(self, child):
        ProjectRelationship.objects.filter(
            parent=self,
            child=child).delete()
        return


class FileManager(models.Manager):
    def live(self, *args, **kwargs):
        base_qs = self.filter(status=constants.LIVE_STATUS)
        return base_qs.filter(*args, **kwargs)


class File(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='files')
    parent = models.ForeignKey('self', verbose_name=_('Parent'), null=True, blank=True,
                               related_name='children')
    heading = models.CharField(_('Heading'), max_length=255)
    slug = models.SlugField(_('Slug'))
    content = models.TextField(_('Content'))
    denormalized_path = models.CharField(_('Denormalized path'), max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(_('Ordering'), default=1)
    status = models.PositiveSmallIntegerField(_('Status'), choices=constants.STATUS_CHOICES,
        default=constants.LIVE_STATUS)

    objects = FileManager()

    class Meta:
        ordering = ('denormalized_path',)

    def __unicode__(self):
        return '%s: %s' % (self.project.name, self.heading)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)

        if self.parent:
            path = '%s/%s' % (self.parent.denormalized_path, self.slug)
        else:
            path = self.slug

        self.denormalized_path = path

        super(File, self).save(*args, **kwargs)

        if self.children:
            def update_children(children):
                for child in children:
                    child.save()
                    update_children(child.children.all())
            update_children(self.children.all())
        #Update modified time on project.
        self.project.save()

    @property
    def depth(self):
        return len(self.denormalized_path.split('/'))

    def create_revision(self, old_content, comment):
        FileRevision.objects.create(
            file=self,
            comment=comment,
            diff=diff(self.content, old_content)
        )

    @property
    def current_revision(self):
        return self.revisions.filter(is_reverted=False)[0]

    def get_html_diff(self, rev_from, rev_to):
        rev_from = self.revisions.get(revision_number=rev_from)
        rev_to = self.revisions.get(revision_number=rev_to)

        diffs = dmp.diff_main(rev_from.diff, rev_to.diff)
        return dmp.diff_prettyHtml(diffs)

    def revert_to(self, revision_number):
        revision = self.revisions.get(revision_number=revision_number)
        revision.apply()

    @property
    def filename(self):
        return os.path.join(
            self.project.path,
            '%s.rst' % self.denormalized_path
        )

    def get_rendered(self):
        return render_to_string('projects/doc_file.rst.html', {'file': self})

    def write_to_disk(self):
        safe_write(self.filename, self.get_rendered())

    @models.permalink
    def get_absolute_url(self):
        return ('docs_detail', [self.project.slug, 'en', 'latest',
                                self.denormalized_path + '.html'])


class FileRevision(models.Model):
    file = models.ForeignKey(File, verbose_name=_('File'), related_name='revisions')
    comment = models.TextField(_('Comment'), blank=True)
    diff = models.TextField(_('Diff'), blank=True)
    created_date = models.DateTimeField(_('Created date'), auto_now_add=True)

    revision_number = models.IntegerField(_('Revision number'))
    is_reverted = models.BooleanField(_('Is reverted'), default=False)

    class Meta:
        ordering = ('-revision_number',)

    def __unicode__(self):
        return self.comment or '%s #%s' % (self.file.heading,
                                           self.revision_number)

    def get_file_content(self):
        """
        Apply the series of diffs after this revision in reverse order,
        bringing the content back to the state it was in this revision
        """
        after = self.file.revisions.filter(
            revision_number__gt=self.revision_number)
        content = self.file.content

        for revision in after:
            patch = dmp.patch_fromText(revision.diff)
            content = dmp.patch_apply(patch, content)[0]

        return content

    def apply(self):
        original_content = self.file.content

        # store the old content on the file
        self.file.content = self.get_file_content()
        self.file.save()

        # mark reverted changesets
        reverted_qs = self.file.revisions.filter(
            revision_number__gt=self.revision_number)
        reverted_qs.update(is_reverted=True)

        # create a new revision
        FileRevision.objects.create(
            file=self.file,
            comment='Reverted to #%s' % self.revision_number,
            diff=diff(self.file.content, original_content)
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            max_rev = self.file.revisions.aggregate(
                max=models.Max('revision_number'))
            if max_rev['max'] is None:
                self.revision_number = 1
            else:
                self.revision_number = max_rev['max'] + 1
        super(FileRevision, self).save(*args, **kwargs)


class ImportedFile(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='imported_files')
    name = models.CharField(_('Name'), max_length=255)
    slug = models.SlugField(_('Slug'))
    path = models.CharField(_('Path'), max_length=255)
    md5 = models.CharField(_('MD5 checksum'), max_length=255)

    @models.permalink
    def get_absolute_url(self):
        return ('docs_detail', [self.project.slug, 'en', 'latest', self.path])

    def __unicode__(self):
        return '%s: %s' % (self.name, self.project)
