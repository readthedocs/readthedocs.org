from django.core.urlresolvers import reverse
from django.db import models
from projects.models import Project

from .constants import BUILD_STATE, BUILD_TYPES


class Version(models.Model):
    project = models.ForeignKey(Project, related_name='versions')
    identifier = models.CharField(max_length=255) # used by the vcs backend
    verbose_name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    built = models.BooleanField(default=False)
    uploaded = models.BooleanField(default=False)

    class Meta:
        unique_together = [('project', 'slug')]
        ordering = ['-verbose_name']

    def __unicode__(self):
        return u"Version %s of %s (%s)" % (self.verbose_name, self.project, self.pk)

    def get_absolute_url(self):
        if not self.built and not self.uploaded:
            return ''
        return reverse('docs_detail', kwargs={
            'project_slug': self.project.slug,
            'lang_slug': 'en',
            'version_slug': self.slug,
            'filename': ''
        })



class VersionAlias(models.Model):
    project = models.ForeignKey(Project, related_name='aliases')
    from_slug = models.CharField(max_length=255, default='')
    to_slug = models.CharField(max_length=255, default='', blank=True)
    largest = models.BooleanField(default=False)

    def __unicode__(self):
        return "Alias for %s: %s -> %s" % (self.project, self.from_slug, self.to_slug)


class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds')
    type = models.CharField(max_length=55, choices=BUILD_TYPES, default='html') 
    date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    setup = models.TextField(null=True, blank=True)
    setup_error = models.TextField(null=True, blank=True)
    output = models.TextField()
    error = models.TextField()
    version = models.ForeignKey(Version, null=True, related_name='builds')
    state = models.CharField(max_length=55, choices=BUILD_STATE, default='finished') 

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

    def __unicode__(self):
        return u"Build %s for %s (%s)" % (self.project,
                                          ' '.join(self.project.users.all().values_list('username', flat=True)),
                                          self.pk)

    @models.permalink
    def get_absolute_url(self):
        return ('builds_detail', [self.project.slug, self.pk])
