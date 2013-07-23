from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext

from projects.models import Project
from builds.models import Version


class SphinxNode(models.Model):
    """
    Original Sphinx Websupport schema:
    id VARCHAR(32) NOT NULL,
    document VARCHAR(256) NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (id)
    """
    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='nodes', null=True)
    version = models.ForeignKey(Version, verbose_name=_('Version'),
                                related_name='nodes', null=True)
    document = models.CharField(_('Path'), max_length=255)
    hash = models.CharField(_('Hash'), max_length=255)
    source = models.TextField(_('Source'))

    def __unicode__(self):
        return "%s on %s" % (self.hash, self.document)

class SphinxComment(models.Model):
    """
    Original Sphinx Websupport schema:

    rating INTEGER NOT NULL,
    time DATETIME NOT NULL,
    text TEXT NOT NULL,
    displayed BOOLEAN,
    username VARCHAR(64),
    proposal TEXT,
    proposal_diff TEXT,
    path VARCHAR(256),
    node_id VARCHAR,
    PRIMARY KEY (id),
    CHECK (displayed IN (0, 1)),
    FOREIGN KEY(node_id) REFERENCES sphinx_nodes (id)
    """

    date = models.DateTimeField(_('Date'), auto_now_add=True)
    rating = models.IntegerField(_('Rating'), default=0)
    # Comments
    text = models.TextField(_('Text'))
    displayed = models.BooleanField(_('Displayed'))
    user = models.ForeignKey(User, blank=True, null=True)
    node = models.ForeignKey(SphinxNode, related_name='comments')

    def __unicode__(self):
        return "%s - %s" % (self.text, self.node)
