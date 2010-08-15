from django.db import models
from django.contrib.auth.models import User

from taggit.managers import TaggableManager

from projects.models import Project, Conf

class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds')
    date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    output = models.TextField()
    error = models.TextField()

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return u"Build %s for %s (%s)" % (self.project, self.project.user, self.pk)

    @models.permalink
    def get_absolute_url(self):
        return ('build_detail', [self.project.slug, self.pk])



