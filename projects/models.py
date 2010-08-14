from django.contrib.auth.models import User
from django.db import models

from taggit.managers import TaggableManager


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    github_repo = models.CharField(max_length=100, blank=True)
    github_login = models.CharField(max_length=100, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    tags = TaggableManager()

    class Meta:
        ordering = ('-modified_date', 'name')

    def __unicode__(self):
        return self.name


class File(models.Model):
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True)
    heading = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    denormalized_path = models.CharField(max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('ordering', 'denormalized_path',)

    def __unicode__(self):
        return '%s: %s' % (self.project.name, self.heading) 
