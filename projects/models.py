from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.functional import memoize

from projects.constants import DEFAULT_THEME_CHOICES, THEME_DEFAULT
from projects.utils import diff, dmp

from taggit.managers import TaggableManager

import os
import fnmatch


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    github_repo = models.CharField(max_length=100, blank=True)
    github_login = models.CharField(max_length=100, blank=True)
    docs_directory = models.CharField(max_length=255, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    tags = TaggableManager()

    class Meta:
        ordering = ('-modified_date', 'name')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('projects_detail', args=[self.user.username, self.slug])

    def user_doc_path(self):
        return os.path.join(settings.DOCROOT, self.user.username, self.slug)
    user_doc_path = property(memoize(user_doc_path, {}, 1))

    def full_html_path(self):
        doc_base = os.path.join(self.user_doc_path, self.slug)
        for possible_path in ['docs', 'doc']:
            for pos_build in ['build', '_build', '.build']:
                if os.path.exists(os.path.join(doc_base, '%s/%s/html' % (possible_path, pos_build))):
                    return os.path.join(doc_base, '%s/%s/html' % (possible_path, pos_build))

    full_html_path = property(memoize(full_html_path, {}, 1))

    def find(self, file):
        matches = []
        for root, dirnames, filenames in os.walk(self.user_doc_path):
          for filename in fnmatch.filter(filenames, file):
              matches.append(os.path.join(root, filename))
        print "finding %s" % file
        return matches

    find = memoize(find, {}, 2)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)
        try:
            conf = self.conf
        except Conf.DoesNotExist:
            Conf.objects.create(project=self)

    @property
    def template_dir(self):
        return os.path.join(settings.SITE_ROOT, 'templates', 'sphinx')

    def get_rendered_conf(self):
        return render_to_string('projects/conf.py.html', {'project': self})

    def write_conf(self):
        conf_py = file(os.path.join(self.conf.path, 'conf.py'), 'w')
        conf_py.write(self.get_rendered_conf())
        conf_py.close()


class Conf(models.Model):
    project = models.OneToOneField(Project, related_name='conf')
    copyright = models.CharField(max_length=255, blank=True)
    theme = models.CharField(max_length=20, choices=DEFAULT_THEME_CHOICES,
                             default=THEME_DEFAULT)
    path = models.CharField(max_length=255, editable=False, null=True)

    def __unicode__(self):
        return '%s config, v. %s' % (self.project.name, self.version)

    @property
    def version(self):
        # TODO: hook into project versioning to retrieve latest ver
        return ''


class File(models.Model):
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    heading = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    denormalized_path = models.CharField(max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('ordering', 'denormalized_path',)

    def __unicode__(self):
        return '%s: %s' % (self.project.name, self.heading)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)

        if self.parent:
            path = '%s%s/' % (self.parent.denormalized_path, self.slug)
        else:
            path = '%s/' % (self.slug)

        self.denormalized_path = path

        super(File, self).save(*args, **kwargs)

        if self.children:
            def update_children(children):
                for child in children:
                    child.save()
                    update_children(child.children.all())
            update_children(self.children.all())
    
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


class FileRevision(models.Model):
    file = models.ForeignKey(File, related_name='revisions')
    comment = models.TextField(blank=True)
    diff = models.TextField(blank=True)

    revision_number = models.IntegerField()
    is_reverted = models.BooleanField(default=False)

    class Meta:
        ordering = ('-revision_number',)

    def __unicode__(self):
        return '%s #%s' % (self.file.heading, self.revision_number)

    def get_file_content(self):
        """
        Apply the series of diffs after this revision in reverse order,
        bringing the content back to the state it was in this revision
        """
        after = self.file.revisions.filter(revision__gt=self.revision_number)
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
        reverted_qs = self.file.revisions.filter(revision__gt=self.revision)
        reverted_qs.update(is_reverted=True)
        
        # create a new revision
        FileRevision.objects.create(
            file=self.file,
            comment='Reverted to #%s' % self.revision,
            diff=diff(self.file.content, original_content)
        )
 
    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                self.revision_number = self.file.current_revision.revision_number + 1
            except IndexError:
                self.revision_number = 1
        super(FileRevision, self).save(*args, **kwargs)
