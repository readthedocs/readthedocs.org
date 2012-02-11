import fnmatch
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from projects import constants
from projects.utils import diff, dmp, safe_write
from projects.utils import highest_version as _highest
from taggit.managers import TaggableManager

from vcs_support.base import VCSProject
from vcs_support.backends import backend_cls
from vcs_support.utils import Lock


class ProjectManager(models.Manager):
    def live(self, *args, **kwargs):
        base_qs = self.filter(skip=False)
        return base_qs.filter(*args, **kwargs)

class ProjectRelationship(models.Model):
    parent = models.ForeignKey('Project', related_name='subprojects')
    child = models.ForeignKey('Project', related_name='superprojects')

    def __unicode__(self):
        return "%s -> %s" % (self.parent, self.child)

    #HACK
    def get_absolute_url(self):
        return "http://%s.readthedocs.org/projects/%s/en/latest/" % (self.parent.slug, self.child.slug)

class Project(models.Model):
    #Auto fields
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    #Generally from conf.py
    users = models.ManyToManyField(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True,
        help_text='The reStructuredText description of the project')
    repo = models.CharField(max_length=100, blank=True,
            help_text='Checkout URL for your code (hg, git, etc.). Ex. https://github.com/ericholscher/django-kong.git')
    repo_type = models.CharField(max_length=10, choices=constants.REPO_CHOICES, default='git')
    project_url = models.URLField(blank=True, help_text='The project\'s homepage', verify_exists=False)
    version = models.CharField(max_length=100, blank=True,
        help_text='Project version these docs apply to, i.e. 1.0a')
    copyright = models.CharField(max_length=255, blank=True,
        help_text='Project copyright information')
    theme = models.CharField(max_length=20,
        choices=constants.DEFAULT_THEME_CHOICES, default=constants.THEME_DEFAULT,
        help_text='<a href="http://sphinx.pocoo.org/theming.html#builtin-themes" target="_blank">Examples</a>')
    suffix = models.CharField(max_length=10, editable=False, default='.rst')
    default_version = models.CharField(max_length=255, default='latest', help_text='The version of your project that / redirects to')
    # In default_branch, None max_lengtheans the backend should choose the appropraite branch. Eg 'master' for git
    default_branch = models.CharField(max_length=255, default=None, null=True,
        blank=True, help_text='What branch "latest" points to. Leave empty to use the default value for your VCS (eg. trunk or master).')
    requirements_file = models.CharField(max_length=255, default=None, null=True, blank=True, help_text='Requires Virtualenv. A pip requirements file needed to build your documentation. Path from the root of your project.')
    documentation_type = models.CharField(max_length=20,
        choices=constants.DOCUMENTATION_CHOICES, default='sphinx',
        help_text='Type of documentation you are building.')
    analytics_code = models.CharField(max_length=50, null=True, blank=True, help_text="Google Analytics Tracking Code. This may slow down your page loads.")

    #Other model data.
    path = models.CharField(help_text="The directory where conf.py lives",
                            max_length=255, editable=False)
    featured = models.BooleanField()
    skip = models.BooleanField()
    use_virtualenv = models.BooleanField(
        help_text="Install your project inside a virtualenv using "
        "setup.py install")
    django_packages_url = models.CharField(max_length=255, blank=True)
    crate_url = models.CharField(max_length=255, blank=True)

    #Subprojects
    related_projects = models.ManyToManyField('self', blank=True, null=True, symmetrical=False, through=ProjectRelationship)

    tags = TaggableManager(blank=True)
    objects = ProjectManager()

    class Meta:
        ordering = ('slug',)

    def __unicode__(self):
        return self.name

    @property
    def subdomain(self):
        return "%s.readthedocs.org" % self.slug#.replace('_', '-')

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
                raise Exception("Model must have slug")
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None):
        version = version_slug or self.get_default_version()
        return reverse('docs_detail', kwargs={
            'project_slug': self.slug,
            'lang_slug': 'en',
            'version_slug': version,
            'filename': '',
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
            print("Could not find conf.py in %s" % self)
            return ''

    def conf_dir(self, version='latest'):
        conf_file = self.conf_file(version)
        if conf_file:
            return conf_file.replace('/conf.py', '')

    @property
    def highest_version(self):
        return _highest(self.versions.filter(active=True))

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
            return self.builds.all()[0]
        except IndexError:
            return None

    def active_versions(self):
        return (self.versions.filter(built=True, active=True) |
                self.versions.filter(active=True, uploaded=True))
    
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
        try:
            return all([user.get_profile().whitelisted for user in self.users.all()])
        except ObjectDoesNotExist:
            #Bare except so we don't have to import user.models.UserProfile
            return False

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
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children')
    heading = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    denormalized_path = models.CharField(max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(default=1)
    status = models.PositiveSmallIntegerField(choices=constants.STATUS_CHOICES,
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
    file = models.ForeignKey(File, related_name='revisions')
    comment = models.TextField(blank=True)
    diff = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    revision_number = models.IntegerField()
    is_reverted = models.BooleanField(default=False)

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
    project = models.ForeignKey(Project, related_name='imported_files')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    path = models.CharField(max_length=255)
    md5 = models.CharField(max_length=255)

    @models.permalink
    def get_absolute_url(self):
        return ('docs_detail', [self.project.slug, 'en', 'latest', self.path])

    def __unicode__(self):
        return '%s: %s' % (self.name, self.project)
