from rest_framework import serializers

from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.projects.models import Project, Domain


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = (
            'id',
            'name', 'slug', 'description', 'language',
            'repo', 'repo_type',
            'default_version', 'default_branch',
            'documentation_type',
            'users',
        )


class ProjectFullSerializer(ProjectSerializer):

    '''Serializer for all fields on project model'''

    class Meta:
        model = Project


class VersionSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    downloads = serializers.DictField(source='get_downloads', read_only=True)

    class Meta:
        model = Version
        fields = (
            'id',
            'project', 'slug',
            'identifier', 'verbose_name',
            'active', 'built',
            'downloads',
        )


class BuildCommandSerializer(serializers.ModelSerializer):
    run_time = serializers.ReadOnlyField()

    class Meta:
        model = BuildCommandResult


class BuildSerializer(serializers.ModelSerializer):

    """Readonly version of the build serializer, used for user facing display"""

    commands = BuildCommandSerializer(many=True, read_only=True)
    state_display = serializers.ReadOnlyField(source='get_state_display')


class VersionFullSerializer(VersionSerializer):

    '''Serializer for all fields on version model'''

    class Meta:
        model = Build
        exclude = ('builder',)


class BuildSerializerFull(BuildSerializer):

    """Writeable Build instance serializer, for admin access by builders"""

    class Meta:
        model = Build


class SearchIndexSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    project = serializers.CharField(max_length=500, required=False)
    version = serializers.CharField(max_length=500, required=False)
    page = serializers.CharField(max_length=500, required=False)


class DomainSerializer(serializers.ModelSerializer):

    class Meta:
        model = Domain
        fields = (
            'id',
            'project',
            'url',
            'canonical',
            'machine',
            'cname',
        )
