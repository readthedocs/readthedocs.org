import json
import requests

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


class WebStorage(StorageBackend):
    """
    A storage class meant to be used by the Sphinx Builder to store nodes.

    This is super inefficient and a hack right now. 
    When in prod we'll store all nodes to be added and send them all up at once like with sync_versions.

    """

    def has_node(self, id):
        url = "http://localhost:8000/websupport/_has_node"
        data = {'node_id': id,}
        headers = {'Content-type': 'application/json'}
        r = requests.get(url, params=data, headers=headers)
        return r.json['exists']

    def add_node(self, id, document, source):
        url = "http://localhost:8000/websupport/_add_node"
        data = {'id': id, 'document': document, 'source': source}
        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers)
        return True
