import django_filters.rest_framework as filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_flex_fields import FlexFieldsModelViewSet

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project

from .filters import ProjectFilter, VersionFilter
from .serializers import ProjectSerializer, VersionSerializer, VersionUpdateSerializer


class APIv3Settings:

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)
    renderer_classes = (JSONRenderer,)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)


class ProjectsViewSet(APIv3Settings, NestedViewSetMixin, FlexFieldsModelViewSet):

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

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(users=self.request.user)


class VersionsViewSet(APIv3Settings, NestedViewSetMixin, FlexFieldsModelViewSet):

    model = Version
    lookup_field = 'slug'
    lookup_url_kwarg = 'version_slug'
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
