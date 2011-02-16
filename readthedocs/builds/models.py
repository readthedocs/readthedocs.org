from django.core.urlresolvers import reverse
from django.db import models
from projects.models import Project


class Version(models.Model):
    project = models.ForeignKey(Project, related_name='versions')
    identifier = models.CharField(max_length=255) # used by the vcs backend
    verbose_name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    built = models.BooleanField(default=False)
    uploaded = models.BooleanField(default=False)

    class Meta:
        unique_together = [('project', 'slug'), ('project', 'identifier')]
        ordering = ['-verbose_name']

    def __unicode__(self):
        return u"Version %s of %s (%s)" % (self.verbose_name, self.project, self.pk)

    def get_absolute_url(self):
        if not self.built and not self.uploaded:
            return ''
        return reverse('docs_detail', kwargs={
            'project_slug': self.project.slug,
            'version_slug': self.slug,
            'filename': ''
        })



class VersionAlias(models.Model):
    project = models.ForeignKey(Project, related_name='aliases')
    from_slug = models.CharField(max_length=255, default='')
    to_slug = models.CharField(max_length=255, default='')

    def __unicode__(self):
        return "Alias for %s: %s -> %s" % (self.project, self.from_slug, self.to_slug)

class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds')
    date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    output = models.TextField()
    error = models.TextField()
    version = models.ForeignKey(Version, null=True, related_name='builds')

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return u"Build %s for %s (%s)" % (self.project, self.project.user, self.pk)

    @models.permalink
    def get_absolute_url(self):
        return ('builds_detail', [self.project.slug, self.pk])
