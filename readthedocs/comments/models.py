"""Models for the comments app."""

from __future__ import absolute_import
from builtins import str
from builtins import object
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from readthedocs.restapi.serializers import VersionSerializer


class DocumentNodeManager(models.Manager):

    def create(self, *args, **kwargs):

        try:
            node_hash = kwargs.pop('hash')
            commit = kwargs.pop('commit')
        except KeyError:
            raise TypeError("You must provide a hash and commit for the initial NodeSnapshot.")

        node = super(DocumentNodeManager, self).create(*args, **kwargs)
        NodeSnapshot.objects.create(commit=commit, hash=node_hash, node=node)

        return node

    def from_hash(self, version_slug, page, node_hash, project_slug=None):
        """Return a node matching a given hash."""
        snapshots = NodeSnapshot.objects.filter(hash=node_hash,
                                                node__version__slug=version_slug,
                                                node__page=page)

        if project_slug:
            snapshots = snapshots.filter(node__project__slug=project_slug)

        if not snapshots.exists():
            raise DocumentNode.DoesNotExist(
                "No node exists on %s with a current hash of %s" % (
                    page, node_hash))

        if snapshots.count() == 1:
            # If we have found only one snapshot, we know we have the correct node.
            node = snapshots[0].node
        else:
            # IF we have found more than one snapshot...
            number_of_nodes = len(set(snapshots.values_list('node')))
            if number_of_nodes == 1:
                # ...and they're all from the same node, then we know we have the proper node.
                node = snapshots[0].node
            else:
                # On the other hand, if they're from different nodes, then we must
                # have different nodes with the same hash (and thus the same content).
                raise NotImplementedError(
                    '''
                There is more than one node with this content on this page.
                In the future, ReadTheDocs will implement an indexing feature
                to allow unique identification of nodes on the same page with the same content.
                ''')
        return node


@python_2_unicode_compatible
class DocumentNode(models.Model):

    """Document node."""

    objects = DocumentNodeManager()

    project = models.ForeignKey('projects.Project', verbose_name=_('Project'),
                                related_name='nodes', null=True)
    version = models.ForeignKey('builds.Version', verbose_name=_('Version'),
                                related_name='nodes', null=True)
    page = models.CharField(_('Path'), max_length=255)

    raw_source = models.TextField(_('Raw Source'))

    def __str__(self):
        return "node %s on %s for %s" % (self.id, self.page, self.project)

    def latest_hash(self):
        return self.snapshots.latest().hash

    def latest_commit(self):
        return self.snapshots.latest().commit

    def visible_comments(self):
        if not self.project.comment_moderation:
            return self.comments.all()
        # non-optimal SQL warning.
        decisions = ModerationAction.objects.filter(
            comment__node=self,
            decision=1,
            date__gt=self.snapshots.latest().date
        )
        valid_comments = self.comments.filter(moderation_actions__in=decisions).distinct()
        return valid_comments

    def update_hash(self, new_hash, commit):
        latest_snapshot = self.snapshots.latest()
        if latest_snapshot.hash == new_hash and latest_snapshot.commit == commit:
            return latest_snapshot
        return self.snapshots.create(hash=new_hash, commit=commit)


class DocumentNodeSerializer(serializers.ModelSerializer):
    version = VersionSerializer()

    current_hash = serializers.CharField(source='latest_hash')
    last_commit = serializers.CharField(source='latest_commit')
    snapshots_count = serializers.CharField(source='snapshots.count')

    class Meta(object):
        model = DocumentNode
        exclude = ('')


@python_2_unicode_compatible
class NodeSnapshot(models.Model):
    date = models.DateTimeField('Publication date', auto_now_add=True)
    hash = models.CharField(_('Hash'), max_length=255)
    node = models.ForeignKey(DocumentNode, related_name="snapshots")
    commit = models.CharField(max_length=255)

    class Meta(object):
        get_latest_by = 'date'
        # Snapshots are *almost* unique_together just for node and hash,
        # but for the possibility that a node's hash might change and then change back
        # in a later commit.
        unique_together = ("hash", "node", "commit")

    def __str__(self):
        return self.hash


# class DocumentCommentManager(models.Manager):
#
#     def visible(self, inquiring_user=None, node=None):
#         if node:
#
#             decisions = ModerationAction.objects.filter(
#                     comment__node=node,
#                     decision=1,
#                     date__gt=self.snapshots.latest().date
#                 )
#                 valid_comments = node.comments.filter(moderation_actions__in=decisions).distinct()
#
#         if not self.project.comment_moderation:
#             return self.comments.all()
#         else:
# non-optimal SQL warning.
#
#             return valid_comments


@python_2_unicode_compatible
class DocumentComment(models.Model):

    """Comment on a ``DocumentNode`` by a user."""

    date = models.DateTimeField(_('Date'), auto_now_add=True)
    rating = models.IntegerField(_('Rating'), default=0)
    text = models.TextField(_('Text'))
    user = models.ForeignKey(User)
    node = models.ForeignKey(DocumentNode, related_name='comments')

    def __str__(self):
        return "%s - %s" % (self.text, self.node)

    def get_absolute_url(self):
        return "/%s" % self.node.latest_hash()

    def moderate(self, user, decision):
        return self.moderation_actions.create(user=user, decision=decision)

    def has_been_approved_since_most_recent_node_change(self):
        try:
            latest_moderation_action = self.moderation_actions.latest()
        except ModerationAction.DoesNotExist:
            # If we have no moderation actions, obviously we're not approved.
            return False

        most_recent_node_change = self.node.snapshots.latest().date

        if latest_moderation_action.date > most_recent_node_change:
            # If we do have an approval action which is newer than the most recent change,
            # we'll return True or False commensurate with its "approved" attribute.
            return latest_moderation_action.approved()
        return False

    def is_orphaned(self):
        raise NotImplementedError('TODO')


class DocumentCommentSerializer(serializers.ModelSerializer):
    node = DocumentNodeSerializer()

    class Meta(object):
        model = DocumentComment
        fields = ('date', 'user', 'text', 'node')

    def perform_create(self):
        pass


@python_2_unicode_compatible
class ModerationActionManager(models.Model):

    def __str__(self):
        return str(self.id)

    def current_approvals(self):
        # pylint: disable=unused-variable
        most_recent_change = self.comment.node.snapshots.latest().date  # noqa


@python_2_unicode_compatible
class ModerationAction(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(DocumentComment, related_name="moderation_actions")
    decision = models.IntegerField(choices=(
        (0, 'No Decision'),
        (1, 'Publish'),
        (2, 'Hide'),
    ))
    date = models.DateTimeField(_('Date'), auto_now_add=True)

    def __str__(self):
        return "%s - %s" % (self.user_id, self.get_decision_display())

    class Meta(object):
        get_latest_by = 'date'

    def approved(self):
        return self.decision == 1


class ModerationActionSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = ModerationAction
        exclude = ()
