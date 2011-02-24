from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.functional import memoize

from projects import constants
from projects.utils import diff, dmp, safe_write
from taggit.managers import TaggableManager
from vcs_support.base import get_backend
from vcs_support.utils import Lock

import fnmatch
import os
import fnmatch
import re

class ProjectManager(models.Manager):
    def live(self, *args, **kwargs):
        base_qs = self.filter(skip=False)
        return base_qs.filter(*args, **kwargs)


class Project(models.Model):
    #Auto fields
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    #Generally from conf.py
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True,
        help_text='restructuredtext description of the project')
    repo = models.CharField(max_length=100, blank=True,
            help_text='URL for your code (hg or git). Ex. http://github.com/ericholscher/django-kong.git')
    repo_type = models.CharField(max_length=10, choices=constants.REPO_CHOICES, default='git')
    project_url = models.URLField(blank=True, help_text='the project\'s homepage')
    version = models.CharField(max_length=100, blank=True,
        help_text='project version these docs apply to, i.e. 1.0a')
    copyright = models.CharField(max_length=255, blank=True,
        help_text='project copyright information')
    theme = models.CharField(max_length=20,
        choices=constants.DEFAULT_THEME_CHOICES, default=constants.THEME_DEFAULT,
        help_text='<a href="http://sphinx.pocoo.org/theming.html#builtin-themes" target="_blank">Examples</a>')
    suffix = models.CharField(max_length=10, editable=False, default='.rst')
    default_version = models.CharField(max_length=255, default='latest')
    # In default_branch, None means the backend should choose the appropraite branch. Eg 'master' for git
    default_branch = models.CharField(max_length=255, default=None, null=True,
        blank=True, help_text='Leave empty to use the default value for your VCS or if your VCS does not support branches.')

    #Other model data.
    path = models.CharField(max_length=255, editable=False)
    featured = models.BooleanField()
    skip = models.BooleanField()
    use_virtualenv = models.BooleanField()
    django_packages_url = models.CharField(max_length=255, blank=True)

    tags = TaggableManager(blank=True)
    objects = ProjectManager()

    class Meta:
        ordering = ('slug',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.slug])

    def get_docs_url(self, version_slug=None):
        version = version_slug or self.get_default_version()
        return reverse('docs_detail', kwargs={
            'project_slug': self.slug,
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

    @property
    def user_doc_path(self):
        return os.path.join(settings.DOCROOT, self.user.username, self.slug)

    @property
    def user_checkout_path(self):
        return os.path.join(self.user_doc_path, self.slug)

    def venv_path(self, version='latest'):
        return os.path.join(self.user_doc_path, 'envs', version)

    def venv_bin(self, version='latest', bin='python'):
        return os.path.join(self.venv_path(version), 'bin', bin)

    @property
    def full_doc_path(self):
        """
        The path to the documentation root in the project.
        """
        doc_base = os.path.join(self.user_doc_path, self.slug)
        for possible_path in ['docs', 'doc', 'Doc']:
            if os.path.exists(os.path.join(doc_base, '%s' % possible_path)):
                return os.path.join(doc_base, '%s' % possible_path)
        #No docs directory, assume a full docs checkout
        return doc_base

    @property
    def full_build_path(self):
        """
        The path to the build html docs in the project.
        """
        doc_path = self.full_doc_path
        for pos_build in ['build', '_build', '.build']:
            if os.path.exists(os.path.join(doc_path, '%s/html' % pos_build)):
                return os.path.join(doc_path, '%s/html' % pos_build)
        #No standard path? Hack one.
        for pos_build in ['index.html']:
            matches = self.find(pos_build)
            if len(matches) > 0:
                return os.path.dirname(matches[0])

    @property
    def rtd_build_path(self):
        """
        The path to the build html docs in the project.
        """
        return os.path.join(self.user_doc_path, 'rtd-builds')

    @property
    def conf_filename(self):
        if self.path:
            return os.path.join(self.path, 'conf.py')
        raise IOError

    @property
    def is_imported(self):
        return bool(self.repo)

    @property
    def has_good_build(self):
        return any([build.success for build in self.builds.all()])

    @property
    def has_versions(self):
        return self.versions.exists()

    @property
    def has_pdf(self, version_slug='latest'):
        return os.path.exists(self.get_pdf_path(version_slug))

    @property
    def sponsored(self):
        non_django_projects = ['fabric', 'easy-thumbnails',
                               'python-storymarket', 'virtualenv',
                               'virtualenvwrapper', 'varnish',
                               'pip']
        if self.slug in non_django_projects \
        or self.slug.startswith('django'):
            #return True
            return False
        return False

    @property
    def working_dir(self):
        return os.path.join(self.user_doc_path, self.slug)

    @property
    def vcs_repo(self):
        if hasattr(self, '_vcs_repo'):
            return self._vcs_repo
        backend = get_backend(self.repo_type)
        if not backend:
            repo = None
        else:
            repo = backend(self)
        self._vcs_repo = repo
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
        return Lock(self.slug, timeout, polling_interval)

    def full_find(self, file):
        """
        A balla API to find files inside of a projects dir.
        """
        matches = []
        for root, dirnames, filenames in os.walk(self.user_checkout_path):
            for filename in fnmatch.filter(filenames, file):
                matches.append(os.path.join(root, filename))
        return matches
    full_find = memoize(full_find, {}, 2)

    def find(self, file):
        """
        A balla API to find files inside of a projects dir.
        """
        matches = []
        for root, dirnames, filenames in os.walk(self.full_doc_path):
            for filename in fnmatch.filter(filenames, file):
                matches.append(os.path.join(root, filename))
        return matches
    find = memoize(find, {}, 2)

    def get_latest_build(self):
        try:
            return self.builds.all()[0]
        except IndexError:
            return None

    def active_versions(self):
        return self.versions.filter(built=True, active=True) | self.versions.filter(active=True, uploaded=True)

    def get_pdf_path(self, version_slug='latest'):
        path = os.path.join(settings.MEDIA_ROOT,
                                'pdf',
                                self.slug,
                                version_slug,
                                '%s.pdf' % self.slug)
        return path


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
            active=True,
            built=True
        )
        if version_qs.exists():
            return self.default_version
        return 'latest'


class FileManager(models.Manager):
    def live(self, *args, **kwargs):
        base_qs = self.filter(status=constants.LIVE_STATUS)
        return base_qs.filter(*args, **kwargs)


class File(models.Model):
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
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
        return ('docs_detail', [self.project.slug, 'en', 'latest', self.denormalized_path + '.html'])


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
        return self.comment or '%s #%s' % (self.file.heading, self.revision_number)

    def get_file_content(self):
        """
        Apply the series of diffs after this revision in reverse order,
        bringing the content back to the state it was in this revision
        """
        after = self.file.revisions.filter(revision_number__gt=self.revision_number)
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
        reverted_qs = self.file.revisions.filter(revision_number__gt=self.revision_number)
        reverted_qs.update(is_reverted=True)

        # create a new revision
        FileRevision.objects.create(
            file=self.file,
            comment='Reverted to #%s' % self.revision_number,
            diff=diff(self.file.content, original_content)
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            max_rev = self.file.revisions.aggregate(max=models.Max('revision_number'))
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
