from rest_framework import serializers

from builds.models import Build, Version
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

class BuildSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()

    class Meta:
        model = Build
        fields = (
            'id',
            'project',
            'commit',
            'type',
            'date',
            'success',
            
        )


class SearchIndexSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    project = serializers.CharField(max_length=500, required=False)
    version = serializers.CharField(max_length=500, required=False)
    page = serializers.CharField(max_length=500, required=False)
