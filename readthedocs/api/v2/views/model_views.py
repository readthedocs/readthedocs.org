"""Endpoints for listing Projects, Versions, Builds, etc."""

import json
import structlog

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.db.models import BooleanField, Case, Value, When
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.oauth.services import GitHubService, registry
from readthedocs.projects.models import Domain, Project
from readthedocs.storage import build_commands_storage

from ..permissions import APIPermission, APIRestrictedPermission, IsOwner
from ..serializers import (
    BuildAdminSerializer,
    BuildCommandSerializer,
    BuildSerializer,
    DomainSerializer,
    ProjectAdminSerializer,
    ProjectSerializer,
    RemoteOrganizationSerializer,
    RemoteRepositorySerializer,
    SocialAccountSerializer,
    VersionAdminSerializer,
    VersionSerializer,
)
from ..utils import (
    ProjectPagination,
    RemoteOrganizationPagination,
    RemoteProjectPagination,
)

log = structlog.get_logger(__name__)


class PlainTextBuildRenderer(BaseRenderer):

    """
    Custom renderer for text/plain format.

    charset is 'utf-8' by default.
    """

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get('response')
        if not response or response.exception:
            return data.get('detail', '').encode(self.charset)
        data = render_to_string(
            'restapi/log.txt',
            {'build': data},
        )
        return data.encode(self.charset)


class DisableListEndpoint:

    """
    Helper to disable APIv2 listing endpoint.

    We are disablng the listing endpoint because it could cause DOS without
    using any type of filtering.

    This class disables these endpoints except:

     - version resource when passing ``?project__slug=``
     - build resource when using ``?commit=``

    All the other type of listings are disabled and return 409 CONFLICT with an
    error message pointing the user to APIv3.
    """

    def list(self, *args, **kwargs):
        # Using private repos will list resources the user has access to.
        if settings.ALLOW_PRIVATE_REPOS:
            return super().list(*args, **kwargs)

        disabled = True

        # NOTE: keep list endpoint that specifies a resource
        if any([
                self.basename == 'version' and 'project__slug' in self.request.GET,
                self.basename == 'build'
                and ('commit' in self.request.GET or 'project__slug' in self.request.GET),
                self.basename == 'project' and 'slug' in self.request.GET,
        ]):
            disabled = False

        if not disabled:
            return super().list(*args, **kwargs)

        return Response(
            {
                'error': 'disabled',
                'msg': (
                    'List endpoint have been disabled due to heavy resource usage. '
                    'Take into account than APIv2 is planned to be deprecated soon. '
                    'Please use APIv3: https://docs.readthedocs.io/page/api/v3.html'
                )
            },
            status=status.HTTP_410_GONE,
        )


class UserSelectViewSet(viewsets.ModelViewSet):

    """
    View set that varies serializer class based on request user credentials.

    Viewsets using this class should have an attribute `admin_serializer_class`,
    which is a serializer that might have more fields that only admin/staff
    users require. If the user is staff, this class will be returned instead.
    """

    def get_serializer_class(self):
        try:
            if (
                self.request.user.is_staff and
                self.admin_serializer_class is not None
            ):
                return self.admin_serializer_class
        except AttributeError:
            pass
        return self.serializer_class

    def get_queryset(self):
        """Use our API manager method to determine authorization on queryset."""
        return self.model.objects.api(self.request.user)


class ProjectViewSet(DisableListEndpoint, UserSelectViewSet):

    """List, filter, etc, Projects."""

    permission_classes = [APIPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = ProjectSerializer
    admin_serializer_class = ProjectAdminSerializer
    model = Project
    pagination_class = ProjectPagination
    filterset_fields = ('slug',)

    @decorators.action(detail=True)
    def translations(self, *_, **__):
        translations = self.get_object().translations.all()
        return Response({
            'translations': ProjectSerializer(translations, many=True).data,
        })

    @decorators.action(detail=True)
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user),
            pk=kwargs['pk'],
        )
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data,
        })

    @decorators.action(detail=True)
    def active_versions(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user),
            pk=kwargs['pk'],
        )
        versions = project.versions(manager=INTERNAL).filter(active=True)
        return Response({
            'versions': VersionSerializer(versions, many=True).data,
        })

    @decorators.action(
        detail=True,
        permission_classes=[permissions.IsAdminUser],
    )
    def token(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user),
            pk=kwargs['pk'],
        )
        token = GitHubService.get_token_for_project(project, force_local=True)
        return Response({
            'token': token,
        })

    @decorators.action(detail=True)
    def canonical_url(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user),
            pk=kwargs['pk'],
        )
        return Response({
            'url': project.get_docs_url(),
        })


class VersionViewSet(DisableListEndpoint, UserSelectViewSet):

    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = VersionSerializer
    admin_serializer_class = VersionAdminSerializer
    model = Version
    filterset_fields = (
        'active',
        'project__slug',
    )


class BuildViewSet(DisableListEndpoint, UserSelectViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer, PlainTextBuildRenderer)
    serializer_class = BuildSerializer
    admin_serializer_class = BuildAdminSerializer
    model = Build
    filterset_fields = ('project__slug', 'commit')

    @decorators.action(
        detail=False,
        permission_classes=[permissions.IsAdminUser],
        methods=['get'],
    )
    def concurrent(self, request, **kwargs):
        project_slug = request.GET.get('project__slug')
        project = get_object_or_404(Project, slug=project_slug)
        limit_reached, concurrent, max_concurrent = Build.objects.concurrent(project)
        data = {
            'limit_reached': limit_reached,
            'concurrent': concurrent,
            'max_concurrent': max_concurrent,
        }
        return Response(data)

    def retrieve(self, *args, **kwargs):
        """
        Retrieves command data from storage.

        This uses files from storage to get the JSON,
        and replaces the ``commands`` part of the response data.
        """
        if not settings.RTD_SAVE_BUILD_COMMANDS_TO_STORAGE:
            return super().retrieve(*args, **kwargs)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if instance.cold_storage:
            storage_path = '{date}/{id}.json'.format(
                date=str(instance.date.date()),
                id=instance.id,
            )
            if build_commands_storage.exists(storage_path):
                try:
                    json_resp = build_commands_storage.open(storage_path).read()
                    data['commands'] = json.loads(json_resp)
                except Exception:
                    log.exception(
                        'Failed to read build data from storage.',
                        path=storage_path,
                    )
        return Response(data)

    @decorators.action(
        detail=True,
        permission_classes=[permissions.IsAdminUser],
        methods=['post'],
    )
    def reset(self, request, **kwargs):
        """Reset the build so it can be re-used when re-trying."""
        instance = self.get_object()
        instance.reset()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BuildCommandViewSet(DisableListEndpoint, UserSelectViewSet):
    parser_classes = [JSONParser, MultiPartParser]
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = BuildCommandSerializer
    model = BuildCommandResult


class DomainViewSet(DisableListEndpoint, UserSelectViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = DomainSerializer
    model = Domain


class RemoteOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteOrganizationSerializer
    model = RemoteOrganization
    pagination_class = RemoteOrganizationPagination

    def get_queryset(self):
        return (
            self.model.objects.api(self.request.user).filter(
                remote_organization_relations__account__provider__in=[
                    service.adapter.provider_id for service in registry
                ]
            ).distinct()
        )


class RemoteRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteRepositorySerializer
    model = RemoteRepository
    pagination_class = RemoteProjectPagination

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.model.objects.none()

        # TODO: Optimize this query after deployment
        query = self.model.objects.api(self.request.user).annotate(
            admin=Case(
                When(
                    remote_repository_relations__user=self.request.user,
                    remote_repository_relations__admin=True,
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        )
        full_name = self.request.query_params.get('full_name')
        if full_name is not None:
            query = query.filter(full_name__icontains=full_name)
        org = self.request.query_params.get('org', None)
        if org is not None:
            query = query.filter(organization__pk=org)

        own = self.request.query_params.get('own', None)
        if own is not None:
            query = query.filter(
                remote_repository_relations__account__provider=own,
                organization=None,
            )

        query = query.filter(
            remote_repository_relations__account__provider__in=[
                service.adapter.provider_id for service in registry
            ],
        ).distinct()

        # optimizes for the RemoteOrganizationSerializer
        query = query.select_related('organization').order_by(
            'organization__name', 'full_name'
        )

        return query


class SocialAccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = SocialAccountSerializer
    model = SocialAccount

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user.pk)
