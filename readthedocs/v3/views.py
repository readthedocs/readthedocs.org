import django_filters.rest_framework
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
# from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from rest_framework_serializer_extensions.views import SerializerExtensionsAPIViewMixin

from readthedocs.projects.models import Project

from .serializers import ProjectSerializer


class APIv3Settings:

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    throttle_classes = (UserRateThrottle, AnonRateThrottle)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)


class ProjectsViewSet(SerializerExtensionsAPIViewMixin, APIv3Settings, ModelViewSet):

    model = Project
    lookup_field = 'slug'
    lookup_url_kwarg = 'project_slug'
    serializer_class = ProjectSerializer
    filterset_fields = (
        'privacy_level',
    )

    def get_queryset(self):
        user = self.request.user
        return user.projects.all()
