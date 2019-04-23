import django_filters.rest_framework as filters
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from rest_flex_fields.views import FlexFieldsMixin
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.metadata import SimpleMetadata
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project

from .filters import BuildFilter, ProjectFilter, VersionFilter
from .mixins import APIAuthMixin
from .renderer import AlphabeticalSortedJSONRenderer
from .serializers import (
    BuildSerializer,
    BuildTriggerSerializer,
    ProjectSerializer,
    UserSerializer,
    VersionSerializer,
    VersionUpdateSerializer,
)


class APIv3Settings:

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)
    renderer_classes = (AlphabeticalSortedJSONRenderer, BrowsableAPIRenderer)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)
    metadata_class = SimpleMetadata


class ProjectsViewSet(APIv3Settings, APIAuthMixin, NestedViewSetMixin,
                      FlexFieldsMixin, ListModelMixin, RetrieveModelMixin,
                      GenericViewSet):

    # Markdown docstring is automatically rendered by BrowsableAPIRenderer.

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
    * List my projects with offset and limit: ``/api/v3/projects/?offset=10&limit=25``
    * Filter list: ``/api/v3/projects/?name__contains=test``
    * Retrieve only needed data: ``/api/v3/projects/?fields=slug,created``
    * Retrieve specific project: ``/api/v3/projects/{project_slug}/``
    * Expand required fields: ``/api/v3/projects/{project_slug}/?expand=active_versions``
    * Translations of a project: ``/api/v3/projects/{project_slug}/translations/``
    * Subprojects of a project: ``/api/v3/projects/{project_slug}/subprojects/``
    * Superproject of a project: ``/api/v3/projects/{project_slug}/superproject/``

    Go to https://docs.readthedocs.io/en/stable/api/v3.html for a complete documentation of the APIv3.
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

        project = None
        if self.request and self.request.user.is_authenticated():
            project = self.request.user.projects.first()
            if project:
                # TODO: make the links clickable when ``kwargs.html=True``
                return mark_safe(description.format(project_slug=project.slug))
        return description

    @action(detail=True, methods=['get'])
    def translations(self, request, project_slug):
        project = self.get_object()
        return self._related_projects(
            project.translations.api(
                user=request.user,
            ),
        )

    @action(detail=True, methods=['get'])
    def superproject(self, request, project_slug):
        project = self.get_object()
        superproject = getattr(project, 'main_project', None)
        data = None
        if superproject:
            data = self.get_serializer(superproject).data
            return Response(data)
        return Response(status=404)

    @action(detail=True, methods=['get'])
    def subprojects(self, request, project_slug):
        project = self.get_object()
        return self._related_projects(
            project.superprojects.api(
                user=request.user,
            ),
        )

    def _related_projects(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VersionsViewSet(APIv3Settings, APIAuthMixin, NestedViewSetMixin,
                      FlexFieldsMixin, ListModelMixin, RetrieveModelMixin,
                      UpdateModelMixin, GenericViewSet):

    model = Version
    lookup_field = 'slug'
    lookup_url_kwarg = 'version_slug'

    # Allow ``.`` (dots) on version slug
    lookup_value_regex = r'[^/]+'

    filterset_class = VersionFilter
    queryset = Version.objects.all()
    permit_list_expands = [
        'last_build',
        'last_build.config',
    ]

    # NOTE: ``NestedViewSetMixin`` is really good, but if the ``project.slug``
    # does not exist it does not return 404, but 200 instead:
    # /api/v3/projects/nonexistent/versions/

    def get_serializer_class(self):
        """
        Return correct serializer depending on the action (GET or PUT/PATCH/POST).
        """
        if self.action in ('list', 'retrieve'):
            return VersionSerializer
        return VersionUpdateSerializer

    def update(self, request, *args, **kwargs):
        """
        Make PUT/PATCH behaves in the same way.

        Force to return 204 is the update was good.
        """

        # NOTE: ``Authorization: `` is mandatory to use this method from
        # Browsable API since SessionAuthentication can't be used because we set
        # ``httpOnly`` on our cookies and the ``PUT/PATCH`` method are triggered
        # via Javascript
        super().update(request, *args, **kwargs)
        return Response(status=204)


class BuildsViewSet(APIv3Settings, APIAuthMixin, NestedViewSetMixin,
                    FlexFieldsMixin, ListModelMixin, RetrieveModelMixin,
                    CreateModelMixin, GenericViewSet):
    model = Build
    lookup_field = 'pk'
    lookup_url_kwarg = 'build_pk'
    filterset_class = BuildFilter
    queryset = Build.objects.all()
    permit_list_expands = [
        'config',
    ]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return BuildSerializer
        return BuildTriggerSerializer

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

        # TODO: refactor this to be a serializer
        # BuildTriggeredSerializer(build, project, version).data
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


class UsersViewSet(APIv3Settings, NestedViewSetMixin, ListModelMixin,
                   RetrieveModelMixin, GenericViewSet):
    model = User
    lookup_field = 'username'
    lookup_url_kwarg = 'user_username'
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        # ``super().get_queryset`` produces the filter by ``NestedViewSetMixin``
        queryset = super().get_queryset()

        if self.detail:
            return queryset

        # give access to the user if it's maintainer of the project
        if self.request.user in self.model.objects.filter(**self.get_parents_query_dict()):
            return queryset

        raise PermissionDenied
