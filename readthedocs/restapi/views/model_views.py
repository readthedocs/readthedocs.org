# -*- coding: utf-8 -*-
"""Endpoints for listing Projects, Versions, Builds, etc."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging

from allauth.socialaccount.models import SocialAccount
from builtins import str
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import BRANCH, TAG
from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.oauth.services import GitHubService, registry
from readthedocs.projects.models import Domain, EmailHook, Project
from readthedocs.projects.version_handling import determine_stable_version

from .. import utils as api_utils
from ..permissions import (
    APIPermission, APIRestrictedPermission, IsOwner, RelatedProjectIsOwner)
from ..serializers import (
    BuildAdminSerializer, BuildCommandSerializer, BuildSerializer,
    DomainSerializer, ProjectAdminSerializer, ProjectSerializer,
    RemoteOrganizationSerializer, RemoteRepositorySerializer,
    SocialAccountSerializer, VersionAdminSerializer, VersionSerializer)

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
            'restapi/log.txt', {'build': data}
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
            if (self.request.user.is_staff and
                    self.admin_serializer_class is not None):
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
    pagination_class = api_utils.ProjectPagination
    filter_fields = ('slug',)

    @decorators.detail_route()
    def valid_versions(self, request, **kwargs):
        """Maintain state of versions that are wanted."""
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        if (not project.num_major or not project.num_minor or
                not project.num_point):
            return Response(
                {
                    'error': 'Project does not support point version control',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        version_strings = project.supported_versions()
        # Disable making old versions inactive for now.
        # project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(verbose_name__in=version_strings).update(
            active=True,
        )
        return Response({
            'flat': version_strings,
        })

    @detail_route()
    def translations(self, *_, **__):
        translations = self.get_object().translations.all()
        return Response({
            'translations': ProjectSerializer(translations, many=True).data,
        })

    @detail_route()
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data,
        })

    @detail_route()
    def active_versions(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        versions = project.versions.filter(active=True)
        return Response({
            'versions': VersionSerializer(versions, many=True).data,
        })

    @decorators.detail_route(permission_classes=[permissions.IsAdminUser])
    def token(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        token = GitHubService.get_token_for_project(project, force_local=True)
        return Response({
            'token': token,
        })

    @decorators.detail_route()
    def canonical_url(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(request.user), pk=kwargs['pk'])
        return Response({
            'url': project.get_docs_url(),
        })

    @decorators.detail_route(
        permission_classes=[permissions.IsAdminUser], methods=['post'])
    def sync_versions(self, request, **kwargs):  # noqa: D205
        """
        Sync the version data in the repo (on the build server).

        Version data in the repo is synced with what we have in the database.

        :returns: the identifiers for the versions that have been deleted.
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
            log.exception('Sync Versions Error')
            return Response(
                {
                    'error': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promoted_version = project.update_stable_version()
        if promoted_version:
            new_stable = project.get_stable_version()
            log.info(
                'Triggering new stable build: {project}:{version}'.format(
                    project=project.slug,
                    version=new_stable.identifier,
                ))
            trigger_build(project=project, version=new_stable)

            # Marking the tag that is considered the new stable version as
            # active and building it if it was just added.
            if (activate_new_stable and
                    promoted_version.slug in added_versions):
                promoted_version.active = True
                promoted_version.save()
                trigger_build(project=project, version=promoted_version)

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
    filter_fields = ('active', 'project__slug',)


class BuildViewSetBase(UserSelectViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer, PlainTextBuildRenderer)
    serializer_class = BuildSerializer
    admin_serializer_class = BuildAdminSerializer
    model = Build
    filter_fields = ('project__slug', 'commit')


class BuildViewSet(SettingsOverrideObject):

    """A pluggable class to allow for build cold storage."""

    _default_class = BuildViewSetBase


class BuildCommandViewSet(UserSelectViewSet):
    permission_classes = [APIRestrictedPermission]
    renderer_classes = (JSONRenderer,)
    serializer_class = BuildCommandSerializer
    model = BuildCommandResult


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer,)
    model = EmailHook

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


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
    pagination_class = api_utils.RemoteOrganizationPagination

    def get_queryset(self):
        return (
            self.model.objects.api(self.request.user).filter(
                account__provider__in=[
                    service.adapter.provider_id for service in registry
                ]))


class RemoteRepositoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = RemoteRepositorySerializer
    model = RemoteRepository
    pagination_class = api_utils.RemoteProjectPagination

    def get_queryset(self):
        query = self.model.objects.api(self.request.user)
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
            ])
        return query


class SocialAccountViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsOwner]
    renderer_classes = (JSONRenderer,)
    serializer_class = SocialAccountSerializer
    model = SocialAccount

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user.pk)
