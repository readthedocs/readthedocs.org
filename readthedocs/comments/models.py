from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from privacy.backend import AdminPermission, AdminNotAuthorized


class DocumentNodeManager(models.Manager):

    def create(self, *args, **kwargs):

        try:
            hash = kwargs.pop('hash')
            commit = kwargs.pop('commit')
        except KeyError:
            raise TypeError("You must provide a hash and commit for the initial NodeSnapshot.")

        node = super(DocumentNodeManager, self).create(*args, **kwargs)
        NodeSnapshot.objects.create(commit=commit, hash=hash, node=node)

        return node

    def from_hash(self, project, version, page, hash):
        snapshot = NodeSnapshot.objects.filter(
            hash=hash,
            node__project=project,
            node__version=version,
            node__page=page,
        )
        return snapshot.latest().node


class DocumentNode(models.Model):

    objects = DocumentNodeManager()

    project = models.ForeignKey('projects.Project', verbose_name=_('Project'),
                                related_name='nodes', null=True)
    version = models.ForeignKey('builds.Version', verbose_name=_('Version'),
                                related_name='nodes', null=True)
    page = models.CharField(_('Path'), max_length=255)

    def __unicode__(self):
        return "node %s on %s for %s" % (self.id, self.page, self.project)

    def save(self, *args, **kwargs):
        pass
        super(DocumentNode, self).save(*args, **kwargs)

    def latest_hash(self):
        return self.snapshots.latest().hash

    def latest_commit(self):
        return self.snapshots.latest().commit

    def visible_comments(self):
        if not self.project.comment_moderation:
            return self.comments.all()
        else:
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
        else:
            return self.snapshots.create(hash=new_hash, commit=commit)


class DocumentNodeSerializer(serializers.ModelSerializer):

    current_hash = serializers.CharField(source='latest_hash')
    last_commit = serializers.CharField(source='latest_commit')
    snapshots_count = serializers.CharField(source='snapshots.count')

    class Meta:
        model = DocumentNode


class NodeSnapshot(models.Model):
    date = models.DateTimeField('Publication date', auto_now_add=True)
    hash = models.CharField(_('Hash'), max_length=255)
    node = models.ForeignKey(DocumentNode, related_name="snapshots")
    commit = models.CharField(max_length=255)

    class Meta:
        get_latest_by = 'date'
        # Snapshots are *almost* unique_together just for node and hash,
        # but for the possibility that a node's hash might change and then change back
        # in a later commit.
        unique_together = ("hash", "node", "commit")


class DocumentComment(models.Model):
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    rating = models.IntegerField(_('Rating'), default=0)
    text = models.TextField(_('Text'))
    user = models.ForeignKey(User)
    node = models.ForeignKey(DocumentNode, related_name='comments')

    def __unicode__(self):
        return "%s - %s" % (self.text, self.node)

    def get_absolute_url(self):
        return "/%s" % self.node.latest_hash()

    def moderate(self, user, decision):
        user_is_cool = AdminPermission.is_admin(user, self.node.project)
        if not user_is_cool:
            raise AdminNotAuthorized
        self.moderation_actions.create(user=user, decision=decision)

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
        else:
            return False

    def is_orphaned(self):
        self.node


class DocumentCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = DocumentComment
        fields = ('date', 'user', 'text', 'node')


class ModerationAction(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(DocumentComment, related_name="moderation_actions")
    decision = models.IntegerField(choices=(
                  (0, 'No Decision'),
                  (1, 'Publish'),
                  (2, 'Hide'),
                  ))
    date = models.DateTimeField(_('Date'), auto_now_add=True)

    class Meta:
        get_latest_by = 'date'

    def approved(self):
        return self.decision == 1
