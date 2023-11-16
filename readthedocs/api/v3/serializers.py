import datetime
import urllib

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_flex_fields import FlexFieldsModelSerializer
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

from readthedocs.builds.models import Build, Version
from readthedocs.core.resolver import Resolver
from readthedocs.core.utils import slugify
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.organizations.models import Organization, Team
from readthedocs.projects.constants import (
    LANGUAGES,
    PROGRAMMING_LANGUAGES,
    REPO_CHOICES,
)
from readthedocs.projects.models import (
    EnvironmentVariable,
    Project,
    ProjectRelationship,
)
from readthedocs.redirects.models import TYPE_CHOICES as REDIRECT_TYPE_CHOICES
from readthedocs.redirects.models import Redirect


class UserSerializer(FlexFieldsModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
        ]


class BaseLinksSerializer(serializers.Serializer):
    def _absolute_url(self, path):
        scheme = "http" if settings.DEBUG else "https"
        domain = settings.PRODUCTION_DOMAIN
        return urllib.parse.urlunparse((scheme, domain, path, "", "", ""))


class BuildCreateSerializer(serializers.ModelSerializer):

    """
    Used when triggering (create action) a ``Build`` for a specific ``Version``.

    This serializer validates that no field is sent at all in the request.
    """

    class Meta:
        model = Build
        fields = []


class BuildLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "projects-builds-detail",
            kwargs={
                "parent_lookup_project__slug": obj.project.slug,
                "build_pk": obj.pk,
            },
        )
        return self._absolute_url(path)

    def get_version(self, obj):
        if obj.version:
            path = reverse(
                "projects-versions-detail",
                kwargs={
                    "parent_lookup_project__slug": obj.project.slug,
                    "version_slug": obj.version.slug,
                },
            )
            return self._absolute_url(path)
        return None

    def get_project(self, obj):
        path = reverse(
            "projects-detail",
            kwargs={
                "project_slug": obj.project.slug,
            },
        )
        return self._absolute_url(path)


class BuildURLsSerializer(BaseLinksSerializer, serializers.Serializer):
    build = serializers.URLField(source="get_full_url")
    project = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()

    def get_project(self, obj):
        path = reverse("projects_detail", kwargs={"project_slug": obj.project.slug})
        return self._absolute_url(path)

    def get_version(self, obj):
        if obj.version:
            path = reverse(
                "project_version_detail",
                kwargs={
                    "project_slug": obj.project.slug,
                    "version_slug": obj.version.slug,
                },
            )
            return self._absolute_url(path)
        return None


class BuildConfigSerializer(FlexFieldsSerializerMixin, serializers.Serializer):

    """
    Render ``Build.config`` property without modifying it.

    .. note::

       Any change on the output of that property will be reflected here,
       which may produce incompatible changes in the API.
    """

    def to_representation(self, instance):
        # For now, we want to return the ``config`` object as it is without
        # manipulating it.
        return instance


class BuildStateSerializer(serializers.Serializer):
    code = serializers.CharField(source="state")
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.state.title()


class BuildSerializer(FlexFieldsModelSerializer):
    project = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    version = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    created = serializers.DateTimeField(source="date")
    finished = serializers.SerializerMethodField()
    success = serializers.SerializerMethodField()
    duration = serializers.IntegerField(source="length")
    state = BuildStateSerializer(source="*")
    _links = BuildLinksSerializer(source="*")
    urls = BuildURLsSerializer(source="*")

    class Meta:
        model = Build
        fields = [
            "id",
            "version",
            "project",
            "created",
            "finished",
            "duration",
            "state",
            "success",
            "error",
            "commit",
            "_links",
            "urls",
        ]

        expandable_fields = {"config": (BuildConfigSerializer,)}

    def get_finished(self, obj):
        if obj.date and obj.length:
            return obj.date + datetime.timedelta(seconds=obj.length)

    def get_success(self, obj):
        """
        Return ``None`` if the build is not finished.

        This is needed because ``default=True`` in the model field.
        """
        if obj.finished:
            return obj.success

        return None


class VersionLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    builds = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "projects-versions-detail",
            kwargs={
                "parent_lookup_project__slug": obj.project.slug,
                "version_slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_builds(self, obj):
        path = reverse(
            "projects-versions-builds-list",
            kwargs={
                "parent_lookup_project__slug": obj.project.slug,
                "parent_lookup_version__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            "projects-detail",
            kwargs={
                "project_slug": obj.project.slug,
            },
        )
        return self._absolute_url(path)


class VersionDashboardURLsSerializer(BaseLinksSerializer, serializers.Serializer):
    edit = serializers.SerializerMethodField()

    def get_edit(self, obj):
        path = reverse(
            "project_version_detail",
            kwargs={
                "project_slug": obj.project.slug,
                "version_slug": obj.slug,
            },
        )
        return self._absolute_url(path)


class VersionURLsSerializer(BaseLinksSerializer, serializers.Serializer):
    documentation = serializers.SerializerMethodField()
    vcs = serializers.URLField(source="vcs_url")
    dashboard = VersionDashboardURLsSerializer(source="*")

    def get_documentation(self, obj):
        return Resolver().resolve_version(
            project=obj.project,
            version=obj,
        )


class VersionSerializer(FlexFieldsModelSerializer):
    ref = serializers.CharField()
    downloads = serializers.SerializerMethodField()
    urls = VersionURLsSerializer(source="*")
    _links = VersionLinksSerializer(source="*")

    class Meta:
        model = Version
        fields = [
            "id",
            "slug",
            "verbose_name",
            "identifier",
            "ref",
            "built",
            "active",
            "hidden",
            "type",
            "downloads",
            "urls",
            "_links",
            "privacy_level",
        ]

        expandable_fields = {"last_build": (BuildSerializer,)}

    def get_downloads(self, obj):
        downloads = obj.get_downloads()
        data = {}

        for k, v in downloads.items():
            if k in ("html", "pdf", "epub"):
                # Keep backward compatibility
                if k == "html":
                    k = "htmlzip"

                data[k] = ("http:" if settings.DEBUG else "https:") + v

        return data


class VersionUpdateSerializer(serializers.ModelSerializer):

    """
    Used when modifying (update action) a ``Version``.

    It allows to change the version states and privacy level only.
    """

    class Meta:
        model = Version
        fields = [
            "active",
            "hidden",
            "privacy_level",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If privacy levels are not allowed,
        # everything is public, we don't allow changing it.
        if not settings.ALLOW_PRIVATE_REPOS:
            self.fields.pop("privacy_level")


class LanguageSerializer(serializers.Serializer):
    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_code(self, language):
        return language

    def get_name(self, language):
        for code, name in LANGUAGES:
            if code == language:
                return name
        return "Unknown"


class ProgrammingLanguageSerializer(serializers.Serializer):
    code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_code(self, programming_language):
        return programming_language

    def get_name(self, programming_language):
        for code, name in PROGRAMMING_LANGUAGES:
            if code == programming_language:
                return name
        return "Unknown"


class ProjectURLsSerializer(BaseLinksSerializer, serializers.Serializer):

    """Serializer with all the user-facing URLs under Read the Docs."""

    documentation = serializers.CharField(source="get_docs_url")
    home = serializers.SerializerMethodField()
    builds = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    def get_home(self, obj):
        path = reverse("projects_detail", kwargs={"project_slug": obj.slug})
        return self._absolute_url(path)

    def get_builds(self, obj):
        path = reverse("builds_project_list", kwargs={"project_slug": obj.slug})
        return self._absolute_url(path)

    def get_versions(self, obj):
        path = reverse("project_version_list", kwargs={"project_slug": obj.slug})
        return self._absolute_url(path)


class RepositorySerializer(serializers.Serializer):
    url = serializers.CharField(source="repo")
    type = serializers.ChoiceField(
        source="repo_type",
        choices=REPO_CHOICES,
    )


class ProjectLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()

    versions = serializers.SerializerMethodField()
    builds = serializers.SerializerMethodField()
    environmentvariables = serializers.SerializerMethodField()
    redirects = serializers.SerializerMethodField()
    subprojects = serializers.SerializerMethodField()
    superproject = serializers.SerializerMethodField()
    translations = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse("projects-detail", kwargs={"project_slug": obj.slug})
        return self._absolute_url(path)

    def get_versions(self, obj):
        path = reverse(
            "projects-versions-list",
            kwargs={
                "parent_lookup_project__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_environmentvariables(self, obj):
        path = reverse(
            "projects-environmentvariables-list",
            kwargs={
                "parent_lookup_project__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_redirects(self, obj):
        path = reverse(
            "projects-redirects-list",
            kwargs={
                "parent_lookup_project__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_builds(self, obj):
        path = reverse(
            "projects-builds-list",
            kwargs={
                "parent_lookup_project__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_subprojects(self, obj):
        path = reverse(
            "projects-subprojects-list",
            kwargs={
                "parent_lookup_parent__slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_superproject(self, obj):
        path = reverse(
            "projects-superproject",
            kwargs={
                "project_slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_translations(self, obj):
        path = reverse(
            "projects-translations-list",
            kwargs={
                "parent_lookup_main_language_project__slug": obj.slug,
            },
        )
        return self._absolute_url(path)


class ProjectCreateSerializerBase(TaggitSerializer, FlexFieldsModelSerializer):

    """Serializer used to Import a Project."""

    repository = RepositorySerializer(source="*")
    homepage = serializers.URLField(source="project_url", required=False)
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Project
        fields = (
            "name",
            "language",
            "programming_language",
            "repository",
            "homepage",
            "tags",
            "privacy_level",
            "external_builds_privacy_level",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If privacy levels are not allowed,
        # everything is public, we don't allow changing it.
        if not settings.ALLOW_PRIVATE_REPOS:
            self.fields.pop("privacy_level")
            self.fields.pop("external_builds_privacy_level")

    def _validate_remote_repository(self, data):
        """
        Validate connection between `Project` and `RemoteRepository`.

        We don't do anything in community, but we do ensure this relationship
        is posible before creating the `Project` on commercial when the
        organization has VCS SSO enabled.

        If we cannot ensure the relationship here, this method should raise a
        `ValidationError`.
        """

    def validate_name(self, value):
        potential_slug = slugify(value)
        if not potential_slug:
            raise serializers.ValidationError(
                _('Invalid project name "{0}": no slug generated.').format(value),
            )
        if Project.objects.filter(slug=potential_slug).exists():
            raise serializers.ValidationError(
                _('Project with slug "{0}" already exists.').format(potential_slug),
            )
        return value

    def validate(self, data):  # pylint: disable=arguments-renamed
        repo = data.get("repo")
        try:
            # We are looking for an exact match of the repository URL entered
            # by the user and any of the known URLs (ssh, clone, html) we have
            # in our database for this remote repository.
            #
            # If the `RemoteRepository` is found, we save it to link with
            # `Project` object after performing its creating.
            query = Q(ssh_url=repo) | Q(clone_url=repo) | Q(html_url=repo)
            remote_repository = RemoteRepository.objects.get(query)
            data.update(
                {
                    "remote_repository": remote_repository,
                }
            )
        except RemoteRepository.DoesNotExist:
            self._validate_remote_repository(data)

        return data

    def create(self, validated_data):
        remote_repository = validated_data.pop("remote_repository", None)
        project = super().create(validated_data)

        # Link the Project with the RemoteRepository if we found it.
        if remote_repository:
            project.remote_repository = remote_repository
            project.save()

        return project


class ProjectCreateSerializer(SettingsOverrideObject):
    _default_class = ProjectCreateSerializerBase


class ProjectUpdateSerializerBase(TaggitSerializer, FlexFieldsModelSerializer):

    """Serializer used to modify a Project once imported."""

    repository = RepositorySerializer(source="*")
    homepage = serializers.URLField(
        source="project_url",
        required=False,
    )
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Project
        fields = (
            # Settings
            "name",
            "repository",
            "language",
            "programming_language",
            "homepage",
            "tags",
            # Advanced Settings -> General Settings
            "default_version",
            "default_branch",
            "analytics_code",
            "analytics_disabled",
            "show_version_warning",
            "versioning_scheme",
            "external_builds_enabled",
            "privacy_level",
            "external_builds_privacy_level",
            # NOTE: we do not allow to change any setting that can be set via
            # the YAML config file.
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If privacy levels are not allowed,
        # everything is public, we don't allow changing it.
        if not settings.ALLOW_PRIVATE_REPOS:
            self.fields.pop("privacy_level")
            self.fields.pop("external_builds_privacy_level")


class ProjectUpdateSerializer(SettingsOverrideObject):
    _default_class = ProjectUpdateSerializerBase


class ProjectSerializer(FlexFieldsModelSerializer):

    """
    Project serializer.

    .. note::

       When using organizations, projects don't have the concept of users.
       But we have organization.owners.
    """

    homepage = serializers.SerializerMethodField()
    language = LanguageSerializer()
    programming_language = ProgrammingLanguageSerializer()
    repository = RepositorySerializer(source="*")
    urls = ProjectURLsSerializer(source="*")
    subproject_of = serializers.SerializerMethodField()
    translation_of = serializers.SerializerMethodField()
    default_branch = serializers.CharField(source="get_default_branch")
    tags = serializers.StringRelatedField(many=True)
    users = UserSerializer(many=True)
    single_version = serializers.BooleanField(source="is_single_version")

    _links = ProjectLinksSerializer(source="*")

    # TODO: adapt these fields with the proper names in the db and then remove
    # them from here
    created = serializers.DateTimeField(source="pub_date")
    modified = serializers.DateTimeField(source="modified_date")

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "created",
            "modified",
            "language",
            "programming_language",
            "homepage",
            "repository",
            "default_version",
            "default_branch",
            "subproject_of",
            "translation_of",
            "urls",
            "tags",
            "privacy_level",
            "external_builds_privacy_level",
            "versioning_scheme",
            # Kept for backwards compatibility,
            # versioning_scheme should be used instead.
            "single_version",
            # NOTE: ``expandable_fields`` must not be included here. Otherwise,
            # they will be tried to be rendered and fail
            # 'active_versions',
            "_links",
            "users",
        ]

        expandable_fields = {
            # NOTE: this has to be a Model method, can't be a
            # ``SerializerMethodField`` as far as I know
            "active_versions": (
                VersionSerializer,
                {
                    "many": True,
                },
            ),
            "organization": (
                "readthedocs.api.v3.serializers.OrganizationSerializer",
                # NOTE: we cannot have a Project with multiple organizations.
                {"source": "organizations.first"},
            ),
            "teams": (
                serializers.SlugRelatedField,
                {
                    "slug_field": "slug",
                    "many": True,
                    "read_only": True,
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When using organizations, projects don't have the concept of users.
        # But we have organization.owners.
        # Set here instead of at the class level,
        # so is easier to test.
        if settings.RTD_ALLOW_ORGANIZATIONS:
            self.fields.pop("users", None)

    def get_homepage(self, obj):
        # Overridden only to return ``None`` when the project_url is ``''``
        return obj.project_url or None

    def get_translation_of(self, obj):
        if obj.main_language_project:
            return self.__class__(obj.main_language_project).data

    def get_subproject_of(self, obj):
        try:
            return self.__class__(obj.superprojects.first().parent).data
        except Exception:
            return None


class SubprojectCreateSerializer(FlexFieldsModelSerializer):

    """Serializer used to define a Project as subproject of another Project."""

    child = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Project.objects.none(),
    )

    class Meta:
        model = ProjectRelationship
        fields = [
            "child",
            "alias",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_project = self.context["parent"]
        user = self.context["request"].user
        self.fields["child"].queryset = self.parent_project.get_subproject_candidates(
            user
        )
        # Give users a better error message.
        self.fields["child"].error_messages["does_not_exist"] = _(
            "Project with {slug_name}={value} is not valid as subproject"
        )

    def validate_alias(self, value):
        # Check there is not a subproject with this alias already
        subproject = self.parent_project.subprojects.filter(alias=value)
        if subproject.exists():
            raise serializers.ValidationError(
                _("A subproject with this alias already exists"),
            )
        return value

    def validate(self, data):  # pylint: disable=arguments-renamed
        self.parent_project.is_valid_as_superproject(serializers.ValidationError)
        return data


class SubprojectLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "projects-subprojects-detail",
            kwargs={
                "parent_lookup_parent__slug": obj.parent.slug,
                "alias_slug": obj.alias,
            },
        )
        return self._absolute_url(path)

    def get_parent(self, obj):
        path = reverse(
            "projects-detail",
            kwargs={
                "project_slug": obj.parent.slug,
            },
        )
        return self._absolute_url(path)


class ChildProjectSerializer(ProjectSerializer):

    """
    Serializer to render a Project when listed under ProjectRelationship.

    It's exactly the same as ``ProjectSerializer`` but without some fields.
    """

    class Meta(ProjectSerializer.Meta):
        fields = [
            field
            for field in ProjectSerializer.Meta.fields
            if field not in ["subproject_of"]
        ]


class SubprojectSerializer(FlexFieldsModelSerializer):

    """Serializer to render a subproject (``ProjectRelationship``)."""

    child = ChildProjectSerializer()
    _links = SubprojectLinksSerializer(source="*")

    class Meta:
        model = ProjectRelationship
        fields = [
            "child",
            "alias",
            "_links",
        ]


class SubprojectDestroySerializer(FlexFieldsModelSerializer):

    """Serializer used to remove a subproject relationship to a Project."""

    class Meta:
        model = ProjectRelationship
        fields = ("alias",)


class RedirectLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "projects-redirects-detail",
            kwargs={
                "parent_lookup_project__slug": obj.project.slug,
                "redirect_pk": obj.pk,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            "projects-detail",
            kwargs={
                "project_slug": obj.project.slug,
            },
        )
        return self._absolute_url(path)


class RedirectSerializerBase(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    created = serializers.DateTimeField(source="create_dt", read_only=True)
    modified = serializers.DateTimeField(source="update_dt", read_only=True)
    _links = RedirectLinksSerializer(source="*", read_only=True)

    type = serializers.ChoiceField(
        source="redirect_type", choices=REDIRECT_TYPE_CHOICES
    )

    class Meta:
        model = Redirect
        fields = [
            "pk",
            "created",
            "modified",
            "project",
            "type",
            "from_url",
            "to_url",
            "_links",
        ]


class RedirectCreateSerializer(RedirectSerializerBase):
    pass


class RedirectDetailSerializer(RedirectSerializerBase):

    """Override RedirectSerializerBase to sanitize the empty fields."""

    from_url = serializers.SerializerMethodField()
    to_url = serializers.SerializerMethodField()

    def get_from_url(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.from_url or None

    def get_to_url(self, obj):
        # Overridden only to return ``None`` when the description is ``''``
        return obj.to_url or None


class EnvironmentVariableLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "projects-environmentvariables-detail",
            kwargs={
                "parent_lookup_project__slug": obj.project.slug,
                "environmentvariable_pk": obj.pk,
            },
        )
        return self._absolute_url(path)

    def get_project(self, obj):
        path = reverse(
            "projects-detail",
            kwargs={
                "project_slug": obj.project.slug,
            },
        )
        return self._absolute_url(path)


class EnvironmentVariableSerializer(serializers.ModelSerializer):
    value = serializers.CharField(write_only=True)
    project = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    _links = EnvironmentVariableLinksSerializer(source="*", read_only=True)

    class Meta:
        model = EnvironmentVariable
        fields = [
            "pk",
            "created",
            "modified",
            "name",
            "value",
            "public",
            "project",
            "_links",
        ]


class OrganizationLinksSerializer(BaseLinksSerializer):
    _self = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()

    def get__self(self, obj):
        path = reverse(
            "organizations-detail",
            kwargs={
                "organization_slug": obj.slug,
            },
        )
        return self._absolute_url(path)

    def get_projects(self, obj):
        path = reverse(
            "organizations-projects-list",
            kwargs={
                "parent_lookup_organizations__slug": obj.slug,
            },
        )
        return self._absolute_url(path)


class TeamSerializer(FlexFieldsModelSerializer):
    # TODO: add ``projects`` as flex field when we have a
    # /organizations/<slug>/teams/<slug>/projects endpoint

    created = serializers.DateTimeField(source="pub_date")
    modified = serializers.DateTimeField(source="modified_date")

    class Meta:
        model = Team
        fields = (
            "name",
            "slug",
            "created",
            "modified",
            "access",
        )

        expandable_fields = {
            "members": (UserSerializer, {"many": True}),
        }


class OrganizationSerializer(FlexFieldsModelSerializer):
    created = serializers.DateTimeField(source="pub_date")
    modified = serializers.DateTimeField(source="modified_date")
    owners = UserSerializer(many=True)

    _links = OrganizationLinksSerializer(source="*")

    class Meta:
        model = Organization
        fields = (
            "name",
            "description",
            "url",
            "slug",
            "email",
            "owners",
            "created",
            "modified",
            "disabled",
            "_links",
        )

        expandable_fields = {
            "projects": (ProjectSerializer, {"many": True}),
            "teams": (TeamSerializer, {"many": True}),
        }


class RemoteOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteOrganization
        fields = [
            "pk",
            "slug",
            "name",
            "avatar_url",
            "url",
            "vcs_provider",
            "created",
            "modified",
        ]
        read_only_fields = fields


class RemoteRepositorySerializer(FlexFieldsModelSerializer):
    admin = serializers.SerializerMethodField("is_admin")

    class Meta:
        model = RemoteRepository
        fields = [
            "pk",
            "name",
            "full_name",
            "description",
            "admin",
            "avatar_url",
            "ssh_url",
            "clone_url",
            "html_url",
            "vcs",
            "vcs_provider",
            "private",
            "default_branch",
            "created",
            "modified",
        ]
        read_only_fields = fields
        expandable_fields = {
            "remote_organization": (
                RemoteOrganizationSerializer,
                {"source": "organization"},
            ),
            "projects": (ProjectSerializer, {"many": True}),
        }

    def is_admin(self, obj):
        request = self.context["request"]

        # Use annotated value from RemoteRepositoryViewSet queryset
        if hasattr(obj, "_admin"):
            return obj._admin

        return obj.remote_repository_relations.filter(
            user=request.user, admin=True
        ).exists()
