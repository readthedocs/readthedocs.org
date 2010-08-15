from django.db import models
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from projects.models import Project

class Bookmark(models.Model):
    project = models.ForeignKey(Project, related_name='bookmarks', null=True)
    user = models.ForeignKey(User, related_name='bookmarks')
    date = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255)
    desc = models.TextField(null=True)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return u"Bookmark %s for %s (%s)" % (self.url, self.user)

    def get_absolute_url(self):
        return self.url

