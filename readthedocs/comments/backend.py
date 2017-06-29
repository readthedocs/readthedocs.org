"""Storage backends for the comments app."""

from __future__ import absolute_import
import json

from django.core import serializers
from sphinx.websupport.storage import StorageBackend

from .models import DocumentNode


class DjangoStorage(StorageBackend):

    """A Sphinx StorageBackend using Django."""

    def get_metadata(self, docname, moderator=None):
        ret_dict = {}
        for node in DocumentNode.objects.filter(page=docname):
            ret_dict[node.latest_hash()] = node.comments.count()
        return ret_dict

    def get_data(self, node_id, username, moderator=None):
        try:
            node = DocumentNode.objects.get(snapshots__hash=node_id)
        except DocumentNode.DoesNotExist:
            return None
        ret_comments = []
        for comment in node.comments.all():
            json_data = json.loads(serializers.serialize("json", [comment]))[0]
            fields = json_data['fields']
            fields['pk'] = json_data['pk']
            ret_comments.append(
                fields
            )

        return {'source': '',
                'comments': ret_comments}
