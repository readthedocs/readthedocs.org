"""Defines serializers for each of our models."""

import re

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
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
            'urlconf',
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

    environment_variables = serializers.SerializerMethodField()
    skip = serializers.SerializerMethodField()

    def get_environment_variables(self, obj):
        """Get all environment variables, including public ones."""
        return {
            variable.name: dict(
                value=variable.value,
                public=variable.public,
            )
            for variable in obj.environmentvariable_set.all()
        }

    def get_skip(self, obj):
        """
        Override ``Project.skip`` to consider more cases whether skip a project.

        We rely on ``.is_active`` manager's method here that encapsulates all
        these possible cases.
        """
        return not Project.objects.is_active(obj)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + (
            'enable_epub_build',
            'enable_pdf_build',
            'conf_py_file',
            'analytics_code',
            'analytics_disabled',
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
            'max_concurrent_builds',
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
            'privacy_level',
            'active',
            'built',
            'downloads',
            'type',
            'has_pdf',
            'has_epub',
            'has_htmlzip',
            'documentation_type',
        )


class VersionAdminSerializer(VersionSerializer):

    """Version serializer that returns admin project data."""

    project = ProjectAdminSerializer()


class BuildCommandSerializer(serializers.ModelSerializer):

    run_time = serializers.ReadOnlyField()

    class Meta:
        model = BuildCommandResult
        exclude = []


class BuildCommandReadOnlySerializer(BuildCommandSerializer):

    """
    Serializer used on GETs to trim the commands' path.

    Remove unreadable paths from the command outputs when returning it from the API.
    We could make this change at build level, but we want to avoid undoable issues from now
    and hack a small solution to fix the immediate problem.

    This converts:
        $ /usr/src/app/checkouts/readthedocs.org/user_builds/
            <container_hash>/<project_slug>/envs/<version_slug>/bin/python
        $ /home/docs/checkouts/readthedocs.org/user_builds/
            <project_slug>/envs/<version_slug>/bin/python
    into
        $ python
    """

    command = serializers.SerializerMethodField()

    def get_command(self, obj):
        project_slug = obj.build.version.project.slug
        version_slug = obj.build.version.slug
        docroot = settings.DOCROOT.rstrip("/")  # remove trailing '/'

        # Remove Docker hash from DOCROOT when running it locally
        # DOCROOT contains the Docker container hash (e.g. b7703d1b5854).
        # We have to remove it from the DOCROOT it self since it changes each time
        # we spin up a new Docker instance locally.
        container_hash = "/"
        if settings.RTD_DOCKER_COMPOSE:
            docroot = re.sub("/[0-9a-z]+/?$", "", settings.DOCROOT, count=1)
            container_hash = "/([0-9a-z]+/)?"

        regex = f"{docroot}{container_hash}{project_slug}/envs/{version_slug}(/bin/)?"
        command = re.sub(regex, "", obj.command, count=1)
        return command


class BuildSerializer(serializers.ModelSerializer):

    """
    Build serializer for user display.

    This is the default serializer for Build objects over read-only operations from regular users.
    Take into account that:

    - It doesn't display internal fields (builder, _config)
    - It's read-only for multiple fields (commands, project_slug, etc)

    Staff users should use either:

    - BuildAdminSerializer for write operations (e.g. builders hitting the API),
    - BuildAdminReadOnlySerializer for read-only actions (e.g. dashboard retrieving build details)
    """

    commands = BuildCommandReadOnlySerializer(many=True, read_only=True)
    project_slug = serializers.ReadOnlyField(source='project.slug')
    version_slug = serializers.ReadOnlyField(source='get_version_slug')
    docs_url = serializers.SerializerMethodField()
    state_display = serializers.ReadOnlyField(source='get_state_display')
    commit_url = serializers.ReadOnlyField(source='get_commit_url')
    # Jsonfield needs an explicit serializer
    # https://github.com/dmkoch/django-jsonfield/issues/188#issuecomment-300439829
    config = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Build
        # `_config` should be excluded to avoid conflicts with `config`
        exclude = ('builder', '_config')

    def get_docs_url(self, obj):
        if obj.version:
            return obj.version.get_absolute_url()
        return None


class BuildAdminSerializer(BuildSerializer):

    """
    Build serializer to update Build objects from build instances.

    It allows write operations on `commands` and display fields (e.g. builder)
    that are allowed for admin purposes only.
    """

    commands = BuildCommandSerializer(many=True, read_only=True)

    class Meta(BuildSerializer.Meta):
        # `_config` should be excluded to avoid conflicts with `config`
        exclude = ('_config',)


class BuildAdminReadOnlySerializer(BuildAdminSerializer):

    """
    Build serializer to retrieve Build objects from the dashboard.

    It uses `BuildCommandReadOnlySerializer` to automatically parse the command
    and trim the useless path.
    """

    commands = BuildCommandReadOnlySerializer(many=True, read_only=True)


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
        exclude = ('email', 'users',)


class RemoteRepositorySerializer(serializers.ModelSerializer):

    """Remote service repository serializer."""

    organization = RemoteOrganizationSerializer()

    # This field does create an additional query per object returned
    matches = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField('is_admin')

    class Meta:
        model = RemoteRepository
        exclude = ('users',)

    def get_matches(self, obj):
        request = self.context['request']
        if request.user is not None and request.user.is_authenticated:
            return obj.matches(request.user)

    def is_admin(self, obj):
        request = self.context['request']

        # Use annotated value from RemoteRepositoryViewSet queryset
        if hasattr(obj, 'admin'):
            return obj.admin

        if request.user and request.user.is_authenticated:
            return obj.remote_repository_relations.filter(
                user=request.user, admin=True
            ).exists()
        return False


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
