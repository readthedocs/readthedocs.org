from django.db import models
from projects.models import Project

class PageView(models.Model):
    project = models.ForeignKey(Project, related_name='page_views')
    url = models.CharField(max_length=255)
    count = models.IntegerField(default=1)


    def __unicode__(self):
        return u"Page views for %s's url %s" % (self.project, self.url)
