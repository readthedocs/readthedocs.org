from readthedocs.search.api.v2.serializers import PageSearchSerializer as PageSearchSerializerBase
from rest_framework import serializers


class PageSearchSerializer(PageSearchSerializerBase):

    project = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("project_alias")
    
    def get_project(self, obj):
        return {
            "slug": obj.project,
            "alias": self.get_project_alias(obj),
        }

    def get_version(self, obj):
        return {
            "slug": obj.version,
        }
