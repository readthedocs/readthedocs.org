import logging

from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from readthedocs.builds.filters import VersionFilter
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.oauth import utils as oauth_utils
from readthedocs.projects.filters import ProjectFilter
from readthedocs.projects.models import Project, EmailHook, Domain
from readthedocs.projects.version_handling import determine_stable_version
from readthedocs.restapi.permissions import APIPermission
from readthedocs.restapi.permissions import RelatedProjectIsOwner
from readthedocs.restapi.serializers import BuildSerializer, ProjectSerializer, VersionSerializer, DomainSerializer
import readthedocs.restapi.utils as api_utils
log = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [APIPermission]
    renderer_classes = (JSONRenderer, JSONPRenderer, BrowsableAPIRenderer)
    serializer_class = ProjectSerializer
    filter_class = ProjectFilter
    model = Project
    paginate_by = 100
    paginate_by_param = 'page_size'
    max_paginate_by = 1000

    def get_queryset(self):
        return self.model.objects.api(self.request.user)

    @decorators.detail_route()
    def valid_versions(self, request, **kwargs):
        """
        Maintain state of versions that are wanted.
        """
        project = get_object_or_404(
            Project.objects.api(self.request.user), pk=kwargs['pk'])
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
    def translations(self, request, pk):
        translations = self.get_object().translations.all()
        return Response({
            'translations': ProjectSerializer(translations, many=True).data
        })

    @detail_route()
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(self.request.user), pk=kwargs['pk'])
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data
        })

    @decorators.detail_route(permission_classes=[permissions.IsAdminUser])
    def token(self, request, **kwargs):
        project = get_object_or_404(
            Project.objects.api(self.request.user), pk=kwargs['pk'])
        token = oauth_utils.get_token_for_project(project, force_local=True)
        return Response({
            'token': token
        })

    @decorators.detail_route(permission_classes=[permissions.IsAdminUser], methods=['post'])
    def sync_versions(self, request, **kwargs):
        """
        Sync the version data in the repo (on the build server) with what we have in the database.

        Returns the identifiers for the versions that have been deleted.
        """
        project = get_object_or_404(
            Project.objects.api(self.request.user), pk=kwargs['pk'])

        # If the currently highest non-prerelease version is active, then make
        # the new latest version active as well.
        old_highest_version = determine_stable_version(project.versions.all())
        if old_highest_version is not None:
            activate_new_stable = old_highest_version.active
        else:
            activate_new_stable = False

        try:
            # Update All Versions
            data = request.DATA
            added_versions = set()
            if 'tags' in data:
                ret_set = api_utils.sync_versions(
                    project=project, versions=data['tags'], type='tag')
                added_versions.update(ret_set)
            if 'branches' in data:
                ret_set = api_utils.sync_versions(
                    project=project, versions=data['branches'], type='branch')
                added_versions.update(ret_set)
            deleted_versions = api_utils.delete_versions(project, data)
        except Exception, e:
            log.exception("Sync Versions Error: %s" % e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            old_stable = project.get_stable_version()
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
        except:
            log.exception("Stable Version Failure", exc_info=True)

        return Response({
            'added_versions': added_versions,
            'deleted_versions': deleted_versions,
        })


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = VersionSerializer
    filter_class = VersionFilter
    model = Version

    def get_queryset(self):
        return self.model.objects.api(self.request.user)

    @decorators.list_route()
    def downloads(self, request, **kwargs):
        version = get_object_or_404(
            Version.objects.api(self.request.user), pk=kwargs['pk'])
        downloads = version.get_downloads(pretty=True)
        return Response({
            'downloads': downloads
        })


class BuildViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = BuildSerializer
    model = Build

    def get_queryset(self):
        return self.model.objects.api(self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = EmailHook

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        return self.model.objects.api(self.request.user)


class DomainViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (RelatedProjectIsOwner,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = DomainSerializer
    model = Domain

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        return self.model.objects.api(self.request.user)
