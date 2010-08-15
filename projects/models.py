from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.functional import memoize

from projects.constants import DEFAULT_THEME_CHOICES, THEME_DEFAULT
from projects.utils import diff, dmp, safe_write

from taggit.managers import TaggableManager

import os
import re
import fnmatch


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True,
        help_text='restructuredtext description of the project')
    repo = models.CharField(max_length=100, blank=True)
    docs_directory = models.CharField(max_length=255, blank=True)
    project_url = models.URLField(blank=True, help_text='the project\'s homepage')
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    version = models.CharField(max_length=20,
        help_text='project version these docs apply to, i.e. 1.0a')
    copyright = models.CharField(max_length=255, blank=True,
        help_text='project copyright information')
    theme = models.CharField(max_length=20, choices=DEFAULT_THEME_CHOICES,
        default=THEME_DEFAULT)
    path = models.CharField(max_length=255, editable=False)
    suffix = models.CharField(max_length=10, editable=False, default='.rst')

    tags = TaggableManager()

    class Meta:
        ordering = ('-modified_date', 'name')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.user.username, self.slug])

    def get_docs_url(self):
        return reverse('docs_detail', args=[self.user.username, self.slug, ''])

    def get_doc_root(self):
        return os.path.join(
            settings.DOCROOT,   # the root of the user builds .../user_build
            self.user.username, # docs are stored using the username as the
            self.slug,          # docs are organized by project
            self.slug,          # code is checked out here
            self.docs_directory # this is the directory where the docs live
        )

    def user_doc_path(self):
        return os.path.join(settings.DOCROOT, self.user.username, self.slug)
    user_doc_path = property(memoize(user_doc_path, {}, 1))

    def full_doc_path(self):
        doc_base = os.path.join(self.user_doc_path, self.slug)
        for possible_path in ['docs', 'doc']:
            if os.path.exists(os.path.join(doc_base, '%s' % possible_path)):
                return os.path.join(doc_base, '%s' % possible_path)
    full_doc_path = property(memoize(full_doc_path, {}, 1))

    def full_html_path(self):
        doc_path = self.full_doc_path
        for pos_build in ['build', '_build', '.build']:
            if os.path.exists(os.path.join(doc_path, '%s/html' % pos_build)):
                return os.path.join(doc_path, '%s/html' % pos_build)

    full_html_path = property(memoize(full_html_path, {}, 1))

    def find(self, file):
        matches = []
        for root, dirnames, filenames in os.walk(self.full_doc_path):
          for filename in fnmatch.filter(filenames, file):
              matches.append(os.path.join(root, filename))
        return matches

    find = memoize(find, {}, 2)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)

    @property
    def template_dir(self):
        return os.path.join(settings.SITE_ROOT, 'templates', 'sphinx')

    def get_index_filename(self):
        return os.path.join(self.path, 'index.rst')

    def get_rendered_index(self):
        return render_to_string('projects/index.rst.html', {'project': self})

    def write_index(self):
        if not self.is_imported:
            safe_write(self.get_index_filename(), self.get_rendered_index())

    @property
    def is_imported(self):
        return bool(self.repo)

    @property
    def repo_type(self):
        if self.is_imported:
            if re.match('(https?://|git://)github', self.repo):
                return 'git'
            elif self.repo.startswith('http://bitbucket'):
                return 'hg'
            elif self.repo.endswith('git'):
                return 'git'

    def get_latest_revisions(self):
        revision_qs = FileRevision.objects.filter(file__project=self)
        return revision_qs.order_by('-created_date')
    
    def get_top_level_files(self):
        return self.files.filter(parent__isnull=True).order_by('ordering')
    
    @property
    def conf_filename(self):
        return os.path.join(self.path, 'conf.py')

    def get_rendered_conf(self):
        return render_to_string('projects/conf.py.html', {'project': self})

    def write_to_disk(self):
        safe_write(self.conf_filename, self.get_rendered_conf())


class File(models.Model):
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    heading = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    denormalized_path = models.CharField(max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(default=1)

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
