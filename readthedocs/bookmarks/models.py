from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext

from builds.models import Version
from projects.models import Project


class Bookmark(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'),
                             related_name='bookmarks')
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='bookmarks')
    version = models.ForeignKey(Version, verbose_name=_('Version'),
                                related_name='bookmarks')
    page = models.CharField(_('Page'), max_length=255)

    date = models.DateTimeField(_('Date'), auto_now_add=True)
    url = models.CharField(_('URL'), max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'project', 'version', 'page')

    def __unicode__(self):
        return ugettext(u"Bookmark %(url)s for %(user)s (%(pk)s)") % {
            'url': self.url,
            'user': self.user,
            'pk': self.pk,
        }

    def get_absolute_url(self):
        return self.url
