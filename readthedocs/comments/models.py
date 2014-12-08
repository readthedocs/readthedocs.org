from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Project
from builds.models import Version


class SphinxNode(models.Model):
    date = models.DateTimeField('Publication date', auto_now_add=True)
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='nodes', null=True)
    version = models.ForeignKey(Version, verbose_name=_('Version'),
                                related_name='nodes', null=True)
    document = models.CharField(_('Path'), max_length=255)
    hash = models.CharField(_('Hash'), max_length=255)
    source = models.TextField(_('Source'))

    def __unicode__(self):
        return "%s on %s for %s" % (self.hash, self.document, self.project)

class SphinxComment(models.Model):
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    rating = models.IntegerField(_('Rating'), default=0)
    # Comments
    text = models.TextField(_('Text'))
    displayed = models.BooleanField(_('Displayed'))
    user = models.ForeignKey(User, blank=True, null=True)
    node = models.ForeignKey(SphinxNode, related_name='comments')

    def __unicode__(self):
        return "%s - %s" % (self.text, self.node)
