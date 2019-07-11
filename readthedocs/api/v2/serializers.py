"""Defines serializers for each of our models."""

from allauth.socialaccount.models import SocialAccount
from rest_framework import serializers

from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Domain, Project


class ProjectSerializer(serializers.ModelSerializer):
    canonical_url = serializers.ReadOnlyField(source='get_docs_url')

    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'language',
            'programming_language',
            'repo',
            'repo_type',
            'default_version',
            'default_branch',
            'documentation_type',
            'users',
            'canonical_url',
        )


class ProjectAdminSerializer(ProjectSerializer):

    """
    Project serializer for admin only access.

    Includes special internal fields that don't need to be exposed through the
    general API, mostly for fields used in the build process
    """

    features = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='feature_id',
    )

    def get_environment_variables(self, obj):
        return {
            variable.name: variable.value
            for variable in obj.environmentvariable_set.all()
        }

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + (
            'enable_epub_build',
            'enable_pdf_build',
            'conf_py_file',
            'analytics_code',
            'cdn_enabled',
            'container_image',
            'container_mem_limit',
            'container_time_limit',
            'install_project',
            'use_system_packages',
            'skip',
            'requirements_file',
            'python_interpreter',
            'features',
            'has_valid_clone',
            'has_valid_webhook',
            'show_advertising',
            'environment_variables',
        )


class VersionSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    downloads = serializers.DictField(source='get_downloads', read_only=True)

    class Meta:
        model = Version
        fields = (
            'id',
            'project',
            'slug',
            'identifier',
            'verbose_name',
            'active',
            'built',
            'downloads',
            'type',
        )


class VersionAdminSerializer(VersionSerializer):

    """Version serializer that returns admin project data."""

    project = ProjectAdminSerializer()


class BuildCommandSerializer(serializers.ModelSerializer):

    run_time = serializers.ReadOnlyField()

    class Meta:
        model = BuildCommandResult
        exclude = ('')


class BuildSerializer(serializers.ModelSerializer):

    """Build serializer for user display, doesn't display internal fields."""

    commands = BuildCommandSerializer(many=True, read_only=True)
    project_slug = serializers.ReadOnlyField(source='project.slug')
    version_slug = serializers.ReadOnlyField(source='version.slug')
    docs_url = serializers.ReadOnlyField(source='version.get_absolute_url')
    state_display = serializers.ReadOnlyField(source='get_state_display')
    vcs_url = serializers.ReadOnlyField(source='version.vcs_url')
    # Jsonfield needs an explicit serializer
    # https://github.com/dmkoch/django-jsonfield/issues/188#issuecomment-300439829
    config = serializers.JSONField(required=False)

    class Meta:
        model = Build
        # `_config` should be excluded to avoid conflicts with `config`
        exclude = ('builder', '_config')


class BuildAdminSerializer(BuildSerializer):

    """Build serializer for display to admin users and build instances."""

    class Meta(BuildSerializer.Meta):
        # `_config` should be excluded to avoid conflicts with `config`
        exclude = ('_config',)


class SearchIndexSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=500)
    project = serializers.CharField(max_length=500, required=False)
    version = serializers.CharField(max_length=500, required=False)
    page = serializers.CharField(max_length=500, required=False)


class DomainSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()

    class Meta:
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

    class Meta:
        model = RemoteOrganization
        exclude = ('json', 'email', 'users')


class RemoteRepositorySerializer(serializers.ModelSerializer):

    """Remote service repository serializer."""

    organization = RemoteOrganizationSerializer()

    # This field does create an additional query per object returned
    matches = serializers.SerializerMethodField()

    class Meta:
        model = RemoteRepository
        exclude = ('json', 'users')

    def get_matches(self, obj):
        request = self.context['request']
        if request.user is not None and request.user.is_authenticated:
            return obj.matches(request.user)


class ProviderSerializer(serializers.Serializer):

    id = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=20)


class SocialAccountSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()
    avatar_url = serializers.URLField(source='get_avatar_url')
    provider = ProviderSerializer(source='get_provider')

    class Meta:
        model = SocialAccount
        exclude = ('extra_data',)

    def get_username(self, obj):
        return (
            obj.extra_data.get('username') or obj.extra_data.get('login')
            # FIXME: which one is GitLab?
        )
