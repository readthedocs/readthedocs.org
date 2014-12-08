import json

from django.core import serializers
from sphinx.websupport.storage import StorageBackend

from .models import SphinxComment, SphinxNode
from projects.models import Project

class DjangoStorage(StorageBackend):
    """
    A Sphinx StorageBackend using Django.
    """

    def has_node(self, id):
        return SphinxNode.objects.filter(hash=id).exists()

    def add_node(self, id, document, source, project, version):
        project_obj = Project.objects.get(slug=project)
        version_obj = project_obj.versions.get(slug=version)
        node, created = SphinxNode.objects.get_or_create(
            hash=id, 
            document=document, 
            source=source,
            project=project_obj,
            version=version_obj,
        )
        return created

    def get_metadata(self, docname, moderator=None):
        ret_dict = {}
        for node in SphinxNode.objects.filter(document=docname):
            ret_dict[node.hash] = node.comments.count()
        return ret_dict

    def get_data(self, node_id, username, moderator=None):
        try:
            node = SphinxNode.objects.get(hash=node_id)
        except SphinxNode.DoesNotExist:
            return None
        ret_comments = []
        for comment in node.comments.all():
            json_data = json.loads(serializers.serialize("json", [comment]))[0]['fields']
            ret_comments.append(
                    json_data
                )

        return {'source': '',
                'comments': ret_comments}

    def add_comment(self, text, displayed, username, time,
                    proposal, node_id, parent_id, moderator):

        node = SphinxNode.objects.get(hash=node_id)
        comment = SphinxComment.objects.create(node=node, text=text, displayed=displayed, rating=0)

        data = json.loads(serializers.serialize("json", [comment]))[0]['fields']
        return data 

