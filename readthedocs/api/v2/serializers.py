"""Defines serializers for each of our models."""


from allauth.socialaccount.models import SocialAccount
from rest_framework import serializers

from readthedocs.api.v2.utils import normalize_build_command
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.core.resolver import Resolver
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Domain, Project


class ProjectSerializer(serializers.ModelSerializer):
    canonical_url = serializers.ReadOnlyField(source="get_docs_url")

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "language",
            "programming_language",
            "repo",
            "repo_type",
            "default_version",
            "default_branch",
            "documentation_type",
            "users",
            "canonical_url",
            "custom_prefix",
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
        slug_field="feature_id",
    )

    environment_variables = serializers.SerializerMethodField()
    skip = serializers.SerializerMethodField()

    def get_environment_variables(self, obj):
        """Get all environment variables, including public ones."""
        return {
            variable.name: {
                "value": variable.value,
                "public": variable.public,
            }
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
            "enable_epub_build",
            "enable_pdf_build",
            "conf_py_file",
            "analytics_code",
            "analytics_disabled",
            "cdn_enabled",
            "container_image",
            "container_mem_limit",
            "container_time_limit",
            "install_project",
            "skip",
            "requirements_file",
            "python_interpreter",
            "features",
            "has_valid_clone",
            "has_valid_webhook",
            "show_advertising",
            "environment_variables",
            "max_concurrent_builds",
            "readthedocs_yaml_path",
        )


class VersionSerializer(serializers.ModelSerializer):

    """
    Version serializer.

    Instead of using directly a ProjectSerializer for the project,
    we user a SerializerMethodField to have more control over the
    serialization of the project, this allows us to optimize the
    serialization of the same project for each version.

    We usually filter all versions that belong to one project,
    so instead of serializing the same project over and over again,
    we cache the serialized project and reuse it for each version.

    Why not just rely on select_related('project')?
    Since the project is the same for all versions most of the time,
    we would be serializing the same project over and over again,
    and ProjectSerializer includes a call to get_docs_url,
    ``users``, and ``features``, get_docs_url we can cached, ``users``
    can be included in a ``prefetch_related`` call,
    but ``features`` is a property with a custom queryset, so it can't be added.

    See https://github.com/readthedocs/readthedocs.org/pull/10460#discussion_r1238928385.
    """

    project = serializers.SerializerMethodField()
    project_serializer_class = ProjectSerializer

    downloads = serializers.DictField(source="get_downloads", read_only=True)

    class Meta:
        model = Version
        fields = [
            "id",
            "project",
            "slug",
            "identifier",
            "verbose_name",
            "privacy_level",
            "active",
            "built",
            "downloads",
            "type",
            "has_pdf",
            "has_epub",
            "has_htmlzip",
            "documentation_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serialized_projects_cache = {}

    def _get_project_serialized(self, obj):
        """Get a serialized project from the cache or create a new one."""
        project = obj.project
        project_serialized = self._serialized_projects_cache.get(project.id)
        if project_serialized:
            return project_serialized

        self._serialized_projects_cache[project.id] = self.project_serializer_class(
            project
        )
        return self._serialized_projects_cache[project.id]

    def get_project(self, obj):
        project_serialized = self._get_project_serialized(obj)
        return project_serialized.data


class VersionAdminSerializer(VersionSerializer):

    """Version serializer that returns admin project data."""

    project_serializer_class = ProjectAdminSerializer
    canonical_url = serializers.SerializerMethodField()
    build_data = serializers.JSONField(required=False, write_only=True, allow_null=True)
    addons = serializers.BooleanField(required=False, write_only=True, allow_null=False)

    def get_canonical_url(self, obj):
        # Use the cached object, since it has some
        # relationships already cached from calling
        # get_docs_url early when serializing the project.
        project = self._get_project_serialized(obj).instance
        return Resolver().resolve_version(
            project=project,
            version=obj,
        )

    class Meta(VersionSerializer.Meta):
        fields = VersionSerializer.Meta.fields + [
            "addons",
            "build_data",
            "canonical_url",
            "machine",
        ]


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
        return normalize_build_command(
            obj.command, obj.build.project.slug, obj.build.version.slug
        )


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
    project_slug = serializers.ReadOnlyField(source="project.slug")
    version_slug = serializers.ReadOnlyField(source="get_version_slug")
    docs_url = serializers.SerializerMethodField()
    state_display = serializers.ReadOnlyField(source="get_state_display")
    commit_url = serializers.ReadOnlyField(source="get_commit_url")
    # Jsonfield needs an explicit serializer
    # https://github.com/dmkoch/django-jsonfield/issues/188#issuecomment-300439829
    config = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Build
        # `_config` should be excluded to avoid conflicts with `config`
        exclude = ("builder", "_config")

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
        exclude = ("_config",)


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
            "id",
            "project",
            "domain",
            "canonical",
            "machine",
            "cname",
        )


class RemoteOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteOrganization
        exclude = (
            "email",
            "users",
        )


class RemoteRepositorySerializer(serializers.ModelSerializer):

    """Remote service repository serializer."""

    organization = RemoteOrganizationSerializer()

    # This field does create an additional query per object returned
    matches = serializers.SerializerMethodField()
    admin = serializers.SerializerMethodField("is_admin")

    class Meta:
        model = RemoteRepository
        exclude = ("users",)

    def get_matches(self, obj):
        request = self.context["request"]
        if request.user is not None and request.user.is_authenticated:
            return obj.matches(request.user)

    def is_admin(self, obj):
        request = self.context["request"]

        # Use annotated value from RemoteRepositoryViewSet queryset
        if hasattr(obj, "admin"):
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
    avatar_url = serializers.URLField(source="get_avatar_url")
    provider = ProviderSerializer(source="get_provider")

    class Meta:
        model = SocialAccount
        exclude = ("extra_data",)

    def get_username(self, obj):
        return (
            obj.extra_data.get("username")
            or obj.extra_data.get("login")
            # FIXME: which one is GitLab?
        )
