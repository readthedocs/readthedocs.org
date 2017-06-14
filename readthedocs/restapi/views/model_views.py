"""Endpoints for listing Projects, Versions, Builds, etc."""

from __future__ import absolute_import
import logging

from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import TAG
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.core.utils import trigger_build
from readthedocs.oauth.services import GitHubService, registry
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Project, EmailHook, Domain
from readthedocs.projects.version_handling import determine_stable_version

from ..permissions import (APIPermission, APIRestrictedPermission,
                           RelatedProjectIsOwner, IsOwner)
from ..serializers import (BuildSerializerFull, BuildSerializer,
                           BuildCommandSerializer, ProjectSerializer,
                           VersionSerializer, DomainSerializer,
                           RemoteOrganizationSerializer,
                           RemoteRepositorySerializer)
from .. import utils as api_utils

log = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):

    """List, filter, etc. Projects."""

    permission_classes = [APIPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = ProjectSerializer
    model = Project
    paginate_by = 100
    paginate_by_param = 'page_size'
    max_paginate_by = 1000

    def get_queryset(self):
        return self.model.objects.api(self.request.user)

    @decorators.detail_route()
    def valid_versions(self, request, **kwargs):
        """Maintain state of versions that are wanted."""
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        if not project.num_major or not project.num_minor or not project.num_point:
            return Response(
                {'error': 'Project does not support point version control'},
                status=status.HTTP_400_BAD_REQUEST)
        version_strings = project.supported_versions()
        # Disable making old versions inactive for now.
        # project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(
            verbose_name__in=version_strings).update(active=True)
        return Response({
            'flat': version_strings,
        })

    @detail_route()
    def translations(self, *_, **__):
        translations = self.get_object().translations.all()
        return Response({
            'translations': ProjectSerializer(translations, many=True).data
        })

    @detail_route()
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data
        })

    @decorators.detail_route(permission_classes=[permissions.IsAdminUser])
    def token(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        token = GitHubService.get_token_for_project(project, force_local=True)
        return Response({
            'token': token
        })

    @decorators.detail_route()
    def canonical_url(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        return Response({
            'url': project.get_docs_url()
        })

    @decorators.detail_route(permission_classes=[permissions.IsAdminUser], methods=['post'])
    def sync_versions(self, request, **kwargs):
        """
        Sync the version data in the repo (on the build server) with what we have in the database.

        Returns the identifiers for the versions that have been deleted.
        """
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])

        # If the currently highest non-prerelease version is active, then make
        # the new latest version active as well.
        old_highest_version = determine_stable_version(project.versions.all())
        if old_highest_version is not None:
            activate_new_stable = old_highest_version.active
        else:
            activate_new_stable = False

        try:
            # Update All Versions
            data = request.data
            added_versions = set()
            if 'tags' in data:
                ret_set = api_utils.sync_versions(
                    project=project, versions=data['tags'], type=TAG)
                added_versions.update(ret_set)
            if 'branches' in data:
                ret_set = api_utils.sync_versions(
                    project=project, versions=data['branches'], type=BRANCH)
                added_versions.update(ret_set)
            deleted_versions = api_utils.delete_versions(project, data)
        except Exception as e:
            log.exception("Sync Versions Error: %s", e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

        promoted_version = project.update_stable_version()
        if promoted_version:
            new_stable = project.get_stable_version()
            log.info(
                "Triggering new stable build: {project}:{version}".format(
                    project=project.slug,
                    version=new_stable.identifier))
            trigger_build(project=project, version=new_stable)

            # Marking the tag that is considered the new stable version as
            # active and building it if it was just added.
            if (
                    activate_new_stable and
                    promoted_version.slug in added_versions):
                promoted_version.active = True
                promoted_version.save()
                trigger_build(project=project, version=promoted_version)

        return Response({
            'added_versions': added_versions,
            'deleted_versions': deleted_versions,
        })


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer,)
    serializer_class = VersionSerializer
    model = Version

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


class BuildViewSet(viewsets.ModelViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    model = Build

    def get_queryset(self):
        return self.model.objects.api(self.request.user)

    def get_serializer_class(self):
        """Vary serializer class based on user status

        This is used to allow write to write-only fields on Build by admin users
        and to not return those fields to non-admin users.
        """
        if self.request.user.is_staff:
            return BuildSerializerFull
        return BuildSerializer


class BuildCommandViewSet(viewsets.ModelViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = BuildCommandSerializer
    model = BuildCommandResult

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer,)
    model = EmailHook

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


class DomainViewSet(viewsets.ModelViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = DomainSerializer
    model = Domain

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


class RemoteOrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteOrganizationSerializer
    model = RemoteOrganization
    paginate_by = 25

    def get_queryset(self):
        return (self.model.objects.api(self.request.user)
                .filter(account__provider__in=[service.adapter.provider_id
                                               for service in registry]))


class RemoteRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteRepositorySerializer
    model = RemoteRepository

    def get_queryset(self):
        query = self.model.objects.api(self.request.user)
        org = self.request.query_params.get('org', None)
        if org is not None:
            query = query.filter(organization__pk=org)
        query = query.filter(account__provider__in=[service.adapter.provider_id
                                                    for service in registry])
        return query

    def get_paginate_by(self):
        return self.request.query_params.get('page_size', 25)
