import json

from sphinx.websupport.storage import StorageBackend
from django.core import serializers


from .models import SphinxComment, SphinxNode

class DjangoStorage(StorageBackend):
    """
    A Sphinx StorageBackend using Django.
    """

    def has_node(self, id):
        return SphinxNode.objects.filter(hash=id).exists()

    def add_node(self, id, document, source):
       created, node = SphinxNode.objects.get_or_create(hash=id, document=document, source=source)
       return created

    def get_metadata(self, docname, moderator=None):
        ret_dict = {}
        for node in SphinxNode.objects.filter(document=docname):
            ret_dict[node.hash] = node.comments.count()
        return ret_dict

    def get_data(self, node_id, username, moderator=None):
        node = SphinxNode.objects.get(hash=node_id)
        ret_comments = []
        for comment in node.comments.all():
            json_data = json.loads(serializers.serialize("json", [comment]))[0]['fields']
            json_data['children'] = []
            ret_comments.append(
                    json_data
                )

        return {'source': '',
                'comments': ret_comments}

    def add_comment(self, text, displayed, username, time,
                    proposal, node_id, parent_id, moderator):
        proposal_diff = None
        proposal_diff_text = None

        node = SphinxNode.objects.get(hash=node_id)
        comment = SphinxComment.objects.create(node=node, text=text, displayed=displayed, rating=0)

        data = json.loads(serializers.serialize("json", [comment]))[0]
        return data 