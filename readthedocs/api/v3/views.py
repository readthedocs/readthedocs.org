import django_filters.rest_framework as filters
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Prefetch
from rest_flex_fields import is_expanded
from rest_flex_fields.views import FlexFieldsMixin
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.metadata import SimpleMetadata
from rest_framework.mixins import CreateModelMixin
from rest_framework.mixins import DestroyModelMixin
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import GenericViewSet
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from readthedocs.api.v2.permissions import ReadOnlyPermission
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.core.views.hooks import trigger_sync_versions
from readthedocs.notifications.models import Notification
from readthedocs.oauth.models import RemoteOrganization
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.models import RemoteRepositoryRelation
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.projects.models import Domain
from readthedocs.projects.models import EnvironmentVariable
from readthedocs.projects.models import Project
from readthedocs.projects.models import ProjectRelationship
from readthedocs.projects.views.mixins import ProjectImportMixin
from readthedocs.redirects.models import Redirect

from .filters import BuildFilter
from .filters import NotificationFilter
from .filters import ProjectFilter
from .filters import RemoteOrganizationFilter
from .filters import RemoteRepositoryFilter
from .filters import VersionFilter
from .mixins import OrganizationQuerySetMixin
from .mixins import ProjectQuerySetMixin
from .mixins import RemoteQuerySetMixin
from .mixins import UpdateChangeReasonMixin
from .mixins import UpdateMixin
from .mixins import UserQuerySetMixin
from .permissions import IsCurrentUser
from .permissions import IsOrganizationAdmin
from .permissions import IsOrganizationAdminMember
from .permissions import IsProjectAdmin
from .renderers import AlphabeticalSortedJSONRenderer
from .serializers import BuildCreateSerializer
from .serializers import BuildSerializer
from .serializers import EnvironmentVariableSerializer
from .serializers import NotificationSerializer
from .serializers import OrganizationSerializer
from .serializers import ProjectCreateSerializer
from .serializers import ProjectSerializer
from .serializers import ProjectUpdateSerializer
from .serializers import RedirectCreateSerializer
from .serializers import RedirectDetailSerializer
from .serializers import RemoteOrganizationSerializer
from .serializers import RemoteRepositorySerializer
from .serializers import SubprojectCreateSerializer
from .serializers import SubprojectDestroySerializer
from .serializers import SubprojectSerializer
from .serializers import TeamSerializer
from .serializers import UserSerializer
from .serializers import VersionSerializer
from .serializers import VersionUpdateSerializer


class APIv3Settings:
    """
    Django REST Framework settings for APIv3.

    Override global DRF settings for APIv3 in particular. All ViewSet should
    inherit from this class to share/apply the same settings all over the APIv3.

    .. note::

        The only settings used from ``settings.REST_FRAMEWORK`` is
        ``DEFAULT_THROTTLE_RATES`` since it's not possible to define here.
    """

    authentication_classes = (TokenAuthentication, SessionAuthentication)

    pagination_class = LimitOffsetPagination
    LimitOffsetPagination.default_limit = 10

    renderer_classes = (AlphabeticalSortedJSONRenderer, BrowsableAPIRenderer)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)
    metadata_class = SimpleMetadata


class ProjectsViewSetBase(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ProjectImportMixin,
    UpdateChangeReasonMixin,
    CreateModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    ReadOnlyModelViewSet,
):
    model = Project
    lookup_field = "slug"
    lookup_url_kwarg = "project_slug"
    filterset_class = ProjectFilter
    permit_list_expands = [
        "active_versions",
        "organization",
        "permissions",
        "teams",
    ]

    def get_permissions(self):
        # Create and list are actions that act on the current user.
        if self.action in ("create", "list"):
            permission_classes = [IsAuthenticated]
        # Actions that change the state of the project require admin permissions on the project.
        elif self.action in ("update", "partial_update", "destroy", "sync_versions"):
            permission_classes = [IsAuthenticated & IsProjectAdmin]
        # Any other action is read-only.
        else:
            permission_classes = [ReadOnlyPermission]
        return [permission() for permission in permission_classes]

    def get_view_name(self):
        # Avoid "Base" in BrowseableAPI view's title
        if self.name:
            return self.name
        return f"Projects {self.suffix}"

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ("list", "retrieve"):
            return ProjectSerializer

        if self.action == "create":
            return ProjectCreateSerializer

        if self.action in ("update", "partial_update"):
            return ProjectUpdateSerializer

        # Default serializer so that sync_versions works with the BrowseableAPI
        return ProjectSerializer

    def get_queryset(self):
        if self.action == "list":
            # When listing, return all the projects where the user is admin.
            queryset = self.admin_projects(self.request.user)
        else:
            queryset = super().get_queryset()

        # This could be a class attribute and managed on the ``ProjectQuerySetMixin`` in
        # case we want to extend the ``prefetch_related`` to other views as
        # well.
        return queryset.select_related(
            "main_language_project",
        ).prefetch_related(
            "tags",
            "users",
            # Prefetch superprojects to avoid N+1 queries when serializing the project.
            Prefetch(
                "superprojects",
                ProjectRelationship.objects.all().select_related("parent"),
                to_attr="_superprojects",
            ),
            # Prefetch the canonical domain to avoid N+1 queries when using the resolver.
            Prefetch(
                "domains",
                Domain.objects.filter(canonical=True),
                to_attr="_canonical_domains",
            ),
        )

    def create(self, request, *args, **kwargs):
        """
        Import Project.

        Override to use a different serializer in the response,
        since it's a different format than the one used for the request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Use a serializer that fully renders a Project,
        # instead of the one used for the request.
        serializer = ProjectSerializer(instance=serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Import Project.

        Trigger our internal mechanism to import a project after it's saved in
        the database.
        """
        project = super().perform_create(serializer)
        self.finish_import_project(self.request, project)

    @action(detail=True, methods=["get"])
    def superproject(self, request, project_slug):
        """Return the superproject of a ``Project``."""
        superproject = self._get_superproject()
        if not superproject:
            return Response(status=status.HTTP_404_NOT_FOUND)
        data = ProjectSerializer(superproject).data
        return Response(data)

    def _get_superproject(self):
        """Get the superproject of the project, taking into consideration the user permissions."""
        project = self.get_object()
        return self.get_queryset().filter(subprojects__child=project).first()

    @action(detail=True, methods=["post"], url_path="sync-versions")
    def sync_versions(self, request, project_slug):
        """
        Kick off a task to sync versions for a project.

        POST to this endpoint to trigger a task that syncs versions for the project.

        This will be used in a button in the frontend,
        but also can be used to trigger a sync from the API.
        """
        project = self.get_object()
        triggered = trigger_sync_versions(project)
        data = {}
        if triggered:
            data.update({"triggered": True})
            code = status.HTTP_202_ACCEPTED
        else:
            data.update({"triggered": False})
            code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=code)


class ProjectsViewSet(SettingsOverrideObject):
    _default_class = ProjectsViewSetBase


class SubprojectRelationshipViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    CreateModelMixin,
    DestroyModelMixin,
    ReadOnlyModelViewSet,
):
    # The main query is done via the ``NestedViewSetMixin`` using the
    # ``parents_query_lookups`` defined when registering the urls.

    model = ProjectRelationship
    lookup_field = "alias"
    lookup_url_kwarg = "alias_slug"
    permission_classes = [ReadOnlyPermission | (IsAuthenticated & IsProjectAdmin)]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on POST,
        it return a serializer to validate just a few fields.
        """
        if self.action == "create":
            return SubprojectCreateSerializer

        if self.action == "destroy":
            return SubprojectDestroySerializer

        return SubprojectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["parent"] = self._get_parent_project()
        return context

    def create(self, request, *args, **kwargs):
        """Define a Project as subproject of another Project."""
        parent = self._get_parent_project()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(parent=parent)
        headers = self.get_success_headers(serializer.data)

        # Use serializer that fully render a the subproject
        serializer = SubprojectSerializer(instance=serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TranslationRelationshipViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ListModelMixin,
    GenericViewSet,
):
    # The main query is done via the ``NestedViewSetMixin`` using the
    # ``parents_query_lookups`` defined when registering the urls.

    model = Project
    lookup_field = "slug"
    lookup_url_kwarg = "project_slug"
    serializer_class = ProjectSerializer
    permission_classes = [ReadOnlyPermission | (IsAuthenticated & IsProjectAdmin)]


# Inherit order is important here. ``NestedViewSetMixin`` has to be on the left
# of ``ProjectQuerySetMixin`` to make calling ``super().get_queryset()`` work
# properly and filter nested dependencies
class VersionsViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    UpdateMixin,
    UpdateModelMixin,
    ReadOnlyModelViewSet,
):
    model = Version
    lookup_field = "slug"
    lookup_url_kwarg = "version_slug"

    # Allow ``.`` (dots) on version slug
    lookup_value_regex = r"[^/]+"

    filterset_class = VersionFilter
    permission_classes = [ReadOnlyPermission | (IsAuthenticated & IsProjectAdmin)]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ("list", "retrieve"):
            return VersionSerializer
        return VersionUpdateSerializer

    def update(self, request, *args, **kwargs):
        """Overridden to call ``post_save`` method on the updated version."""
        # Get the current value before updating.
        version = self.get_object()
        was_active = version.active
        result = super().update(request, *args, **kwargs)
        # Get the updated version.
        version = self.get_object()
        version.post_save(was_active=was_active)
        return result

    def get_queryset(self):
        """Overridden to allow internal versions only."""
        return super().get_queryset().exclude(type=EXTERNAL)


class BuildsViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ReadOnlyModelViewSet,
):
    model = Build
    lookup_field = "pk"
    lookup_url_kwarg = "build_pk"
    serializer_class = BuildSerializer
    filterset_class = BuildFilter
    permission_classes = [ReadOnlyPermission | (IsAuthenticated & IsProjectAdmin)]
    permit_list_expands = [
        "config",
    ]


class BuildsCreateViewSet(BuildsViewSet, CreateModelMixin):
    def get_serializer_class(self):
        if self.action == "create":
            return BuildCreateSerializer

        return super().get_serializer_class()

    def create(self, request, **kwargs):  # pylint: disable=arguments-differ
        project = self._get_parent_project()
        version = self._get_parent_version()
        build_retry = None
        commit = None

        if version.is_external:
            # We use the last build for a version here as we want to update VCS
            # providers and need to reference the latest commit to do so.
            build_retry = version.last_build
            if build_retry:
                commit = build_retry.commit

        _, build = trigger_build(
            project=project,
            version=version,
            commit=commit,
        )

        # TODO: refactor this to be a serializer
        # BuildTriggeredSerializer(build, project, version).data
        data = {
            "build": BuildSerializer(build).data,
            "project": ProjectSerializer(project).data,
            "version": VersionSerializer(version).data,
        }

        if build:
            data.update({"triggered": True})
            code = status.HTTP_202_ACCEPTED
        else:
            data.update({"triggered": False})
            code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=code)


class NotificationsForUserViewSet(
    APIv3Settings,
    FlexFieldsMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    """
    Endpoint to return all the notifications related to the logged in user.

    Hitting this endpoint while logged in will return notifications attached to:

     - User making the request
     - Organizations where the user is owner/member
     - Projects where the user is admin/member
    """

    model = Notification
    serializer_class = NotificationSerializer

    # Override global permissions here because it doesn't not make sense to hit
    # this endpoint without being logged in. We can't use our
    # ``CommonPermissions`` because it requires the endpoint to be nested under
    # ``projects``
    permission_classes = (IsAuthenticated,)
    filterset_class = NotificationFilter

    def get_queryset(self):
        return Notification.objects.for_user(self.request.user, resource="all")


class NotificationsProjectViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    model = Notification
    lookup_field = "pk"
    lookup_url_kwarg = "notification_pk"
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    # We don't want to show notifications to users that don't have admin access to the project.
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get_queryset(self):
        project = self._get_parent_project()
        return project.notifications.all()


class NotificationsBuildViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    model = Notification
    lookup_field = "pk"
    lookup_url_kwarg = "notification_pk"
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    # We need to show build notifications to anonymous users
    # on public builds (the queryset will filter them out).
    # We allow project admins to edit notifications.
    permission_classes = [ReadOnlyPermission | (IsAuthenticated & IsProjectAdmin)]

    def get_queryset(self):
        build = self._get_parent_build()
        return build.notifications.all()


class RedirectsViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    ModelViewSet,
):
    model = Redirect
    lookup_field = "pk"
    lookup_url_kwarg = "redirect_pk"
    permission_classes = (IsAuthenticated & IsProjectAdmin,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related("project")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RedirectCreateSerializer
        return RedirectDetailSerializer

    def perform_create(self, serializer):
        # Inject the project from the URL into the serializer
        serializer.validated_data.update(
            {
                "project": self._get_parent_project(),
            }
        )
        serializer.save()


class EnvironmentVariablesViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    ProjectQuerySetMixin,
    FlexFieldsMixin,
    CreateModelMixin,
    DestroyModelMixin,
    ReadOnlyModelViewSet,
):
    model = EnvironmentVariable
    lookup_field = "pk"
    lookup_url_kwarg = "environmentvariable_pk"
    serializer_class = EnvironmentVariableSerializer
    permission_classes = (IsAuthenticated & IsProjectAdmin,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related("project")

    def perform_create(self, serializer):
        # Inject the project from the URL into the serializer
        serializer.validated_data.update(
            {
                "project": self._get_parent_project(),
            }
        )
        serializer.save()


class RemoteRepositoryViewSet(
    APIv3Settings, RemoteQuerySetMixin, FlexFieldsMixin, ListModelMixin, GenericViewSet
):
    model = RemoteRepository
    serializer_class = RemoteRepositorySerializer
    filterset_class = RemoteRepositoryFilter
    permission_classes = (IsAuthenticated,)
    permit_list_expands = ["remote_organization"]

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                # This field will be used by the serializer.
                _admin=Exists(
                    RemoteRepositoryRelation.objects.filter(
                        remote_repository=OuterRef("pk"),
                        user=self.request.user,
                        admin=True,
                    )
                )
            )
        )

        if is_expanded(self.request, "remote_organization"):
            queryset = queryset.select_related("organization")

        return queryset.order_by("organization__name", "full_name").distinct()


class RemoteOrganizationViewSet(APIv3Settings, RemoteQuerySetMixin, ListModelMixin, GenericViewSet):
    model = RemoteOrganization
    serializer_class = RemoteOrganizationSerializer
    filterset_class = RemoteOrganizationFilter
    permission_classes = (IsAuthenticated,)


class UsersViewSet(
    APIv3Settings,
    GenericViewSet,
):
    # NOTE: this viewset is only useful for nested URLs required for notifications:
    # /api/v3/users/<username>/notifications/
    # However, accessing to /api/v3/users/ or /api/v3/users/<username>/ will return 404.
    # We can implement these endpoints when we need them, tho.

    model = User
    serializer_class = UserSerializer
    queryset = User.objects.none()
    permission_classes = (IsAuthenticated,)
    # We are using the username as the lookup field,
    # by default, DRF does not allow dots and `/`,
    # but we allow usernames to have dots.
    lookup_value_regex = "[^/]+"


class NotificationsUserViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    UserQuerySetMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    model = Notification
    lookup_field = "pk"
    lookup_url_kwarg = "notification_pk"
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    permission_classes = [IsAuthenticated & IsCurrentUser]

    def get_queryset(self):
        # Filter the queryset by only notifications attached to the particular user
        # that's making the request to this endpoint
        content_type = ContentType.objects.get_for_model(User)
        return Notification.objects.filter(
            attached_to_content_type=content_type,
            attached_to_id=self.request.user.pk,
        )


class OrganizationsViewSetBase(
    APIv3Settings,
    GenericViewSet,
):
    # TODO: migrate code from corporate here.
    # NOTE: this viewset is only useful for nested URLs required for notifications:
    # /api/v3/organizations/<slug>/notifications/
    # However, accessing to /api/v3/organizations/ or /api/v3/organizations/<slug>/ will return 404.
    # We can implement these endpoints when we need them, tho.
    # Also note that Read the Docs for Business expose this endpoint already.

    model = Organization
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.none()
    permission_classes = (IsAuthenticated,)


class OrganizationsViewSet(SettingsOverrideObject):
    _default_class = OrganizationsViewSetBase


class OrganizationsProjectsViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    OrganizationQuerySetMixin,
    FlexFieldsMixin,
    ListModelMixin,
    GenericViewSet,
):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated & IsOrganizationAdminMember]
    # We don't need to expand the organization, it's already known.
    permit_list_expands = []

    def get_view_name(self):
        if self.name:
            return self.name
        return f"Organizations Projects {self.suffix}"


class OrganizationsTeamsViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    OrganizationQuerySetMixin,
    FlexFieldsMixin,
    ListModelMixin,
    GenericViewSet,
):
    model = Team
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated & IsOrganizationAdmin]
    permit_list_expands = ["members"]

    def get_queryset(self):
        organization = self._get_parent_organization()
        return organization.teams.all()


class NotificationsOrganizationViewSet(
    APIv3Settings,
    NestedViewSetMixin,
    OrganizationQuerySetMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    model = Notification
    lookup_field = "pk"
    lookup_url_kwarg = "notification_pk"
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    permission_classes = [IsAuthenticated & IsOrganizationAdmin]

    def get_queryset(self):
        organization = self._get_parent_organization()
        return organization.notifications.all()
