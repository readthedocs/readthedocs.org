import django_filters.rest_framework as filters
from django.utils.safestring import mark_safe
from rest_flex_fields.views import FlexFieldsMixin
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.metadata import SimpleMetadata
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet, ModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project, EnvironmentVariable, ProjectRelationship
from readthedocs.projects.views.mixins import ProjectImportMixin
from readthedocs.redirects.models import Redirect


from .filters import BuildFilter, ProjectFilter, VersionFilter
from .mixins import ProjectQuerySetMixin, UpdateMixin
from .permissions import PublicDetailPrivateListing, IsProjectAdmin
from .renderers import AlphabeticalSortedJSONRenderer
from .serializers import (
    BuildCreateSerializer,
    BuildSerializer,
    EnvironmentVariableSerializer,
    ProjectSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    RedirectCreateSerializer,
    RedirectDetailSerializer,
    SubprojectCreateSerializer,
    SubprojectSerializer,
    SubprojectDestroySerializer,
    VersionSerializer,
    VersionUpdateSerializer,
)


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
    permission_classes = (PublicDetailPrivateListing,)

    pagination_class = LimitOffsetPagination
    LimitOffsetPagination.default_limit = 10

    renderer_classes = (AlphabeticalSortedJSONRenderer, BrowsableAPIRenderer)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)
    metadata_class = SimpleMetadata


class ProjectsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                      FlexFieldsMixin, ProjectImportMixin, CreateModelMixin,
                      UpdateMixin, UpdateModelMixin,
                      ReadOnlyModelViewSet):

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    filterset_class = ProjectFilter
    queryset = Project.objects.all()
    permit_list_expands = [
        'active_versions',
        'active_versions.last_build',
        'active_versions.last_build.config',
    ]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ('list', 'retrieve', 'superproject'):
            # NOTE: ``superproject`` is the @action defined in the
            # ProjectViewSet that returns the superproject of a project.
            return ProjectSerializer

        if self.action == 'create':
            return ProjectCreateSerializer

        if self.action in ('update', 'partial_update'):
            return ProjectUpdateSerializer

    def get_queryset(self):
        # Allow hitting ``/api/v3/projects/`` to list their own projects
        if self.basename == 'projects' and self.action == 'list':
            # We force returning ``Project`` objects here because it's under the
            # ``projects`` view.
            return self.admin_projects(self.request.user)

        # This could be a class attribute and managed on the ``ProjectQuerySetMixin`` in
        # case we want to extend the ``prefetch_related`` to other views as
        # well.
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            'related_projects',
            'domains',
            'tags',
            'users',
        )

    def create(self, request, *args, **kwargs):
        """
        Import Project.

        Override to use a different serializer in the response.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Use serializer that fully render a Project
        serializer = ProjectSerializer(instance=serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        Import Project.

        Trigger our internal mechanism to import a project after it's saved in
        the database.
        """
        project = serializer.save()
        self.finish_import_project(self.request, project)

    @action(detail=True, methods=['get'])
    def superproject(self, request, project_slug):
        """Return the superproject of a ``Project``."""
        project = self.get_object()
        try:
            superproject = project.superprojects.first().parent
            data = self.get_serializer(superproject).data
            return Response(data)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SubprojectRelationshipViewSet(APIv3Settings, NestedViewSetMixin,
                                    ProjectQuerySetMixin, FlexFieldsMixin,
                                    CreateModelMixin, DestroyModelMixin,
                                    ReadOnlyModelViewSet):

    # The main query is done via the ``NestedViewSetMixin`` using the
    # ``parents_query_lookups`` defined when registering the urls.

    model = ProjectRelationship
    lookup_field = 'alias'
    lookup_url_kwarg = 'alias_slug'
    queryset = ProjectRelationship.objects.all()

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on POST,
        it return a serializer to validate just a few fields.
        """
        if self.action == 'create':
            return SubprojectCreateSerializer

        if self.action == 'destroy':
            return SubprojectDestroySerializer

        return SubprojectSerializer

    def create(self, request, *args, **kwargs):
        """Define a Project as subproject of another Project."""
        parent = self._get_parent_project()
        serializer = self.get_serializer(parent=parent, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(parent=parent)
        headers = self.get_success_headers(serializer.data)

        # Use serializer that fully render a the subproject
        serializer = SubprojectSerializer(instance=serializer.instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TranslationRelationshipViewSet(APIv3Settings, NestedViewSetMixin,
                                     ProjectQuerySetMixin, FlexFieldsMixin,
                                     ListModelMixin, GenericViewSet):

    # The main query is done via the ``NestedViewSetMixin`` using the
    # ``parents_query_lookups`` defined when registering the urls.

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()


# Inherit order is important here. ``NestedViewSetMixin`` has to be on the left
# of ``ProjectQuerySetMixin`` to make calling ``super().get_queryset()`` work
# properly and filter nested dependencies
class VersionsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                      FlexFieldsMixin, UpdateMixin,
                      UpdateModelMixin, ReadOnlyModelViewSet):

    model = Version
    lookup_field = 'slug'
    lookup_url_kwarg = 'version_slug'

    # Allow ``.`` (dots) on version slug
    lookup_value_regex = r'[^/]+'

    filterset_class = VersionFilter
    queryset = Version.internal.all()
    permit_list_expands = [
        'last_build',
        'last_build.config',
    ]

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action.

        For GET it returns a serializer with many fields and on PUT/PATCH/POST,
        it return a serializer to validate just a few fields.
        """
        if self.action in ('list', 'retrieve'):
            return VersionSerializer
        return VersionUpdateSerializer


class BuildsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                    FlexFieldsMixin, ReadOnlyModelViewSet):

    model = Build
    lookup_field = 'pk'
    lookup_url_kwarg = 'build_pk'
    serializer_class = BuildSerializer
    filterset_class = BuildFilter
    queryset = Build.internal.all()
    permit_list_expands = [
        'config',
    ]


class BuildsCreateViewSet(BuildsViewSet, CreateModelMixin):

    def get_serializer_class(self):
        if self.action == 'create':
            return BuildCreateSerializer

        return super().get_serializer_class()

    def create(self, request, **kwargs):  # pylint: disable=arguments-differ
        project = self._get_parent_project()
        version = self._get_parent_version()

        _, build = trigger_build(project, version=version)

        # TODO: refactor this to be a serializer
        # BuildTriggeredSerializer(build, project, version).data
        data = {
            'build': BuildSerializer(build).data,
            'project': ProjectSerializer(project).data,
            'version': VersionSerializer(build.version).data,
        }

        if build:
            data.update({'triggered': True})
            code = status.HTTP_202_ACCEPTED
        else:
            data.update({'triggered': False})
            code = status.HTTP_400_BAD_REQUEST
        return Response(data=data, status=code)


class RedirectsViewSet(APIv3Settings, NestedViewSetMixin, ProjectQuerySetMixin,
                       FlexFieldsMixin, ModelViewSet):
    model = Redirect
    lookup_field = 'pk'
    lookup_url_kwarg = 'redirect_pk'
    queryset = Redirect.objects.all()
    permission_classes = (IsAuthenticated & IsProjectAdmin,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('project')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RedirectCreateSerializer
        return RedirectDetailSerializer

    def perform_create(self, serializer):
        # Inject the project from the URL into the serializer
        serializer.validated_data.update({
            'project': self._get_parent_project(),
        })
        serializer.save()


class EnvironmentVariablesViewSet(APIv3Settings, NestedViewSetMixin,
                                  ProjectQuerySetMixin, FlexFieldsMixin,
                                  CreateModelMixin, DestroyModelMixin,
                                  ReadOnlyModelViewSet):
    model = EnvironmentVariable
    lookup_field = 'pk'
    lookup_url_kwarg = 'environmentvariable_pk'
    queryset = EnvironmentVariable.objects.all()
    serializer_class = EnvironmentVariableSerializer
    permission_classes = (IsAuthenticated & IsProjectAdmin,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('project')

    def perform_create(self, serializer):
        # Inject the project from the URL into the serializer
        serializer.validated_data.update({
            'project': self._get_parent_project(),
        })
        serializer.save()
