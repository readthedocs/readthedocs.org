from django.db import models
from django.utils.translation import ugettext, ugettext_lazy as _
from projects.models import Project

class PageView(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'), related_name='page_views')
    url = models.CharField(_('URL'), max_length=255)
    count = models.IntegerField(_('Count'), default=1)

    class Meta:
        ordering = ('-count',)

    def __unicode__(self):
        return ugettext(u"Page views for %(project)s's url %(url)s") % {
            'project': self.project,
            'url': self.url
        }

    @models.permalink
    def get_absolute_url(self):
        return ('docs_detail', [self.project.slug, 'latest', self.url])
