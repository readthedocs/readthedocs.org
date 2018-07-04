from rest_framework import serializers

from readthedocs.projects.models import Project


class PageSearchSerializer(serializers.Serializer):
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()

    def get_link(self, obj):
        projects_info = self.context.get('projects_info')
        if projects_info:
            project_data = projects_info[obj.project]
            docs_url = project_data['docs_url']
            return docs_url + obj.path

    def get_highlight(self, obj):
        highlight = getattr(obj.meta, 'highlight', None)
        if highlight:
            return highlight.to_dict()
