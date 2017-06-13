"""Defines serializers for each of our models."""

from __future__ import absolute_import
from builtins import object

from rest_framework import serializers

from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.projects.models import Project, Domain
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository


class ProjectSerializer(serializers.ModelSerializer):
    canonical_url = serializers.ReadOnlyField(source='get_docs_url')

    class Meta(object):
        model = Project
        fields = (
            'id',
            'name', 'slug', 'description', 'language',
            'repo', 'repo_type',
            'default_version', 'default_branch',
            'documentation_type',
            'users',
            'canonical_url',
        )


class VersionSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    downloads = serializers.DictField(source='get_downloads', read_only=True)

    class Meta(object):
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

    class Meta(object):
        model = BuildCommandResult
        exclude = ('')


class BuildSerializer(serializers.ModelSerializer):

    """Readonly version of the build serializer, used for user facing display"""

    commands = BuildCommandSerializer(many=True, read_only=True)
    state_display = serializers.ReadOnlyField(source='get_state_display')

    class Meta(object):
        model = Build
        exclude = ('builder',)


class BuildSerializerFull(BuildSerializer):

    """Writeable Build instance serializer, for admin access by builders"""

    class Meta(object):
        model = Build
        exclude = ('')


class SearchIndexSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    project = serializers.CharField(max_length=500, required=False)
    version = serializers.CharField(max_length=500, required=False)
    page = serializers.CharField(max_length=500, required=False)


class DomainSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()

    class Meta(object):
        model = Domain
        fields = (
            'id',
            'project',
            'domain',
            'canonical',
            'machine',
            'cname',
        )


class RemoteOrganizationSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = RemoteOrganization
        exclude = ('json', 'email', 'users')


class RemoteRepositorySerializer(serializers.ModelSerializer):

    """Remote service repository serializer"""

    organization = RemoteOrganizationSerializer()
    matches = serializers.SerializerMethodField()

    class Meta(object):
        model = RemoteRepository
        exclude = ('json', 'users')

    def get_matches(self, obj):
        request = self.context['request']
        if request.user is not None and request.user.is_authenticated():
            return obj.matches(request.user)
