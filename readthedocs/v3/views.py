from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
import django_filters.rest_framework as filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_flex_fields.views import FlexFieldsMixin

from readthedocs.core.utils import trigger_build
from readthedocs.builds.models import Version, Build
from readthedocs.projects.models import Project
from rest_framework.metadata import SimpleMetadata
from .filters import ProjectFilter, VersionFilter, BuildFilter
from .serializers import ProjectSerializer, VersionSerializer, VersionUpdateSerializer, BuildSerializer


class APIv3Settings:

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)
    metadata_class = SimpleMetadata


class ProjectsViewSet(APIv3Settings, NestedViewSetMixin, FlexFieldsMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):

    """
    Endpoints related to ``Project`` objects.

    * Listing objects.
    * Detailed object.

    Retrieving only needed data using ``?fields=`` URL attribute is allowed.

    ### Filters

    Allowed via URL attributes:

    * slug
    * slug__contains
    * name
    * name__contains

    ### Expandable fields

    There are some fields that are not returned by default because they are
    expensive to calculate. Although, they are available for those cases where
    they are needed.

    Allowed via ``?expand=`` URL attribue:

    * users
    * active_versions
    * active_versions.last_build
    * active_versions.last_build.confg


    ### Examples:

    * List my projects: ``/api/v3/projects/``
    * Filter list: ``/api/v3/projects/?name__contains=test``
    * Retrieve only needed data: ``/api/v3/projects/?fields=slug,created``
    * Retrieve specific project: ``/api/v3/projects/{project_slug}/``
    * Expand required fields: ``/api/v3/projects/{project_slug}/?expand=active_versions``
    * Translations of a projects: ``/api/v3/projects/{project_slug}/translations/``
    * Subprojects of a projects: ``/api/v3/projects/{project_slug}/subprojects/``
    * Superprojects of a projects: ``/api/v3/projects/{project_slug}/superprojects/``
    """

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    queryset = Project.objects.all()
    permit_list_expands = [
        'users',
        'active_versions',
        'active_versions.last_build',
        'active_versions.last_build.config',
    ]

    # NOTE: accessing a existent project when we don't have permissions to
    # access it, returns 404 instead of 403.

    def get_view_description(self, *args, **kwargs):
        """
        Make valid links for the user's documentation browseable API.

        If the user has already one project, we pick the first and make all the
        links for that project. Otherwise, we default to the placeholder.
        """
        description = super().get_view_description(*args, **kwargs)
        project = self.request.user.projects.first()

        # TODO: make the links clickable when ``kwargs.html=True``

        if project:
            return mark_safe(description.format(
                project_slug=project.slug,
            ))
        return description

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(users=self.request.user)

    @action(detail=True, methods=['get'])
    def translations(self, request, project_slug):
        project = self.get_object()
        return self._related_projects(project.translations.all())

    @action(detail=True, methods=['get'])
    def superprojects(self, request, project_slug):
        project = self.get_object()
        return self._related_projects(project.superprojects.all())

    @action(detail=True, methods=['get'])
    def subprojects(self, request, project_slug):
        project = self.get_object()
        return self._related_projects(project.subprojects.all())

    def _related_projects(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VersionsViewSet(APIv3Settings, NestedViewSetMixin, FlexFieldsMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):

    model = Version
    lookup_field = 'slug'
    lookup_url_kwarg = 'version_slug'

    # Allow ``.`` (dots) on version slug
    lookup_value_regex = r'[^/]+'

    serializer_class = VersionSerializer
    filterset_class = VersionFilter
    queryset = Version.objects.all()
    permit_list_expands = [
        'last_build',
        'last_build.config',
    ]

    # NOTE: ``NestedViewSetMixin`` is really good, but if the ``project.slug``
    # does not exist it does not return 404, but 200 instead:
    # /api/v3/projects/nonexistent/versions/

    def get_queryset(self):
        # ``super().get_queryset`` produces the filter by ``NestedViewSetMixin``
        queryset = super().get_queryset()

        # we force to filter only by the versions the user has access to
        user = self.request.user
        queryset = queryset.filter(project__users=user)
        return queryset

    def partial_update(self, request, pk=None, **kwargs):
        version = self.get_object()
        serializer = VersionUpdateSerializer(
            version,
            data=request.data,
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=204)

        return Response(data=serializer.errors, status=400)


class BuildsViewSet(APIv3Settings, NestedViewSetMixin, FlexFieldsMixin, ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet):
    model = Build
    lookup_field = 'pk'
    lookup_url_kwarg = 'build_pk'
    serializer_class = BuildSerializer
    filterset_class = BuildFilter
    queryset = Build.objects.all()
    permit_list_expands = [
        'config',
    ]

    # TODO: browsable API shows the BuildSerializer for POST method, but it
    # should be empty. This can be achieved by using a custom ``metadata_class``
    # and overriding the ``actions`` field

    def get_queryset(self):
        # ``super().get_queryset`` produces the filter by ``NestedViewSetMixin``
        queryset = super().get_queryset()

        # we force to filter only by the versions the user has access to
        user = self.request.user
        queryset = queryset.filter(project__users=user)
        return queryset

    def create(self, request, **kwargs):
        parent_lookup_project__slug = kwargs.get('parent_lookup_project__slug')
        parent_lookup_version__slug = kwargs.get('parent_lookup_version__slug')

        version = None
        project = get_object_or_404(
            Project,
            slug=parent_lookup_project__slug,
            users=request.user,
        )

        if parent_lookup_version__slug:
            version = get_object_or_404(
                project.versions.all(),
                slug=parent_lookup_version__slug,
            )

        _, build = trigger_build(project, version=version)
        data = {
            'build': BuildSerializer(build).data,
            'project': ProjectSerializer(project).data,
            'version': VersionSerializer(build.version).data,
        }

        if build:
            data.update({'triggered': True})
            status = 202
        else:
            data.update({'triggered': False})
            status = 400
        return Response(data=data, status=status)
