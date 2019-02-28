import django_filters.rest_framework as filters
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_flex_fields import FlexFieldsModelViewSet

from readthedocs.projects.models import Project
from readthedocs.restapi.permissions import IsOwner

from .filters import ProjectFilter
from .serializers import ProjectSerializer


class APIv3Settings:

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated, IsOwner)
    renderer_classes = (JSONRenderer,)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (filters.DjangoFilterBackend,)


class ProjectsViewSet(APIv3Settings, FlexFieldsModelViewSet):

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    filterset_class = ProjectFilter
    permit_list_expands = [
        'users',
        'active_versions',
        'active_versions.last_build',
        'active_versions.last_build.config',
    ]

    def get_queryset(self):
        user = self.request.user
        return user.projects.all()
