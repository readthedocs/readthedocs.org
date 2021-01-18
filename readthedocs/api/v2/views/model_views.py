"""Endpoints for listing Projects, Versions, Builds, etc."""

import json
import logging

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import INTERNAL
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.builds.tasks import sync_versions_task
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.oauth.services import GitHubService, registry
from readthedocs.projects.models import Domain, Project

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

log = logging.getLogger(__name__)


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


class ProjectViewSet(UserSelectViewSet):

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

    @decorators.action(
        detail=True,
        permission_classes=[permissions.IsAdminUser],
        methods=['post'],
    )
    def sync_versions(self, request, **kwargs):  # noqa
        """
        Sync the version data in the repo (on the build server).

        Version data in the repo is synced with what we have in the database.

        :returns: the identifiers for the versions that have been deleted.

        .. note::

           This endpoint is deprecated in favor of `sync_versions_task`.
        """
        project = get_object_or_404(
            Project.objects.api(request.user),
            pk=kwargs['pk'],
        )

        added_versions = []
        deleted_versions = []

        try:
            data = request.data
            # Calling the task synchronically to keep backward compatibility
            added_versions, deleted_versions = sync_versions_task(
                project_pk=project.pk,
                tags_data=data.get('tags', []),
                branches_data=data.get('branches', []),
            )
        except Exception as e:
            log.exception('Sync Versions Error')
            return Response(
                {
                    'error': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'added_versions': added_versions,
            'deleted_versions': deleted_versions,
        })


class VersionViewSet(UserSelectViewSet):

    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = VersionSerializer
    admin_serializer_class = VersionAdminSerializer
    model = Version
    filterset_fields = (
        'active',
        'project__slug',
    )


class BuildViewSet(UserSelectViewSet):
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
            storage = get_storage_class(settings.RTD_BUILD_COMMANDS_STORAGE)()
            storage_path = '{date}/{id}.json'.format(
                date=str(instance.date.date()),
                id=instance.id,
            )
            if storage.exists(storage_path):
                try:
                    json_resp = storage.open(storage_path).read()
                    data['commands'] = json.loads(json_resp)
                except Exception:
                    log.exception(
                        'Failed to read build data from storage. path=%s.',
                        storage_path,
                    )
        return Response(data)


class BuildCommandViewSet(UserSelectViewSet):
    parser_classes = [JSONParser, MultiPartParser]
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = BuildCommandSerializer
    model = BuildCommandResult


class DomainViewSet(UserSelectViewSet):
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
                account__provider__in=[
                    service.adapter.provider_id for service in registry
                ],
            )
        )


class RemoteRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteRepositorySerializer
    model = RemoteRepository
    pagination_class = RemoteProjectPagination

    def get_queryset(self):
        query = self.model.objects.api(self.request.user)
        full_name = self.request.query_params.get('full_name')
        if full_name is not None:
            query = query.filter(full_name__icontains=full_name)
        org = self.request.query_params.get('org', None)
        if org is not None:
            query = query.filter(organization__pk=org)

        own = self.request.query_params.get('own', None)
        if own is not None:
            query = query.filter(
                account__provider=own,
                organization=None,
            )

        query = query.filter(
            account__provider__in=[
                service.adapter.provider_id for service in registry
            ],
        )

        # optimizes for the RemoteOrganizationSerializer
        query = query.select_related('organization')

        return query


class SocialAccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = SocialAccountSerializer
    model = SocialAccount

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user.pk)
