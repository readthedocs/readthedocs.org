from rest_framework import serializers

from builds.models import Version
from projects.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    downloads = serializers.CharField(source='get_downloads', read_only=True)

    class Meta:
        model = Project
        fields = (
            'id',
            'name', 'slug', 'description', 'language',
            'repo', 'repo_type',
            'default_version', 'default_branch',
            'documentation_type',
            'users',
            'downloads',
        )


class ProjectFullSerializer(ProjectSerializer):
    '''Serializer for all fields on project model'''

    class Meta:
        model = Project


class VersionSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()

    class Meta:
        model = Version
        fields = (
            'id',
            'project', 'slug',
            'identifier', 'verbose_name',
            'active', 'built',
            )


class VersionFullSerializer(VersionSerializer):
    '''Serializer for all fields on version model'''

    project = ProjectFullSerializer()

    class Meta:
        model = Version


class SearchIndexSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    project = serializers.CharField(max_length=500, required=False)
    version = serializers.CharField(max_length=500, required=False)
    page = serializers.CharField(max_length=500, required=False)
