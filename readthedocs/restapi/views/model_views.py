import logging

from django.shortcuts import get_object_or_404

from rest_framework import decorators, permissions, viewsets, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from builds.models import Build, Version
from builds.filters import VersionFilter
from core.utils import trigger_build
from oauth import utils as oauth_utils
from projects.models import Project, EmailHook
from projects.filters import ProjectFilter

from restapi.serializers import BuildSerializer, ProjectSerializer, VersionSerializer
from restapi.permissions import RelatedProjectIsOwner
import restapi.utils as api_utils

log = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, JSONPRenderer, BrowsableAPIRenderer)
    serializer_class = ProjectSerializer
    filter_class = ProjectFilter
    model = Project
    paginate_by = 100
    paginate_by_param = 'page_size'
    max_paginate_by = 1000

    def get_queryset(self):
        return self.model.objects.public(self.request.user)

    @decorators.link()
    def valid_versions(self, request, **kwargs):
        """
        Maintain state of versions that are wanted.
        """
        project = get_object_or_404(Project.objects.public(self.request.user), pk=kwargs['pk'])
        if not project.num_major or not project.num_minor or not project.num_point:
            return Response({'error': 'Project does not support point version control'}, status=status.HTTP_400_BAD_REQUEST)
        version_strings = project.supported_versions(flat=True)
        # Disable making old versions inactive for now.
        # project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(verbose_name__in=version_strings).update(active=True)
        return Response({
            'flat': version_strings,
        })

    @decorators.link()
    def translations(self, request, **kwargs):
        project = get_object_or_404(Project.objects.public(self.request.user), pk=kwargs['pk'])
        queryset = project.translations.all()
        return Response({
            'translations': ProjectSerializer(queryset, many=True).data
        })

    @decorators.link()
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(Project.objects.public(self.request.user), pk=kwargs['pk'])
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data
        })

    @decorators.link(permission_classes=[permissions.IsAdminUser])
    def token(self, request, **kwargs):
        project = get_object_or_404(Project.objects.public(self.request.user), pk=kwargs['pk'])
        token = oauth_utils.get_token_for_project(project, force_local=True)
        return Response({
            'token': token
        })

    @decorators.action(permission_classes=[permissions.IsAdminUser])
    def sync_versions(self, request, **kwargs):
        """
        Sync the version data in the repo (on the build server) with what we have in the database.

        Returns the identifiers for the versions that have been deleted.
        """
        project = get_object_or_404(Project.objects.public(self.request.user), pk=kwargs['pk'])
        try:
            # Update All Versions
            data = request.DATA
            added_versions = set()
            if 'tags' in data:
                ret_set = api_utils.sync_versions(project=project, versions=data['tags'], type='tag')
                added_versions.update(ret_set)
            if 'branches' in data:
                ret_set = api_utils.sync_versions(project=project, versions=data['branches'], type='branch')
                added_versions.update(ret_set)
            deleted_versions = api_utils.delete_versions(project, data)
        except Exception, e:
            log.exception("Sync Versions Error: %s" % e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update Stable Version
            version_strings = project.supported_versions(flat=True)
            if version_strings:
                new_stable = version_strings[-1]
                new_stable = project.versions.get(verbose_name=new_stable)
                stable = project.versions.filter(slug='stable')
                if stable.exists():
                    stable_obj = stable[0]
                    if (new_stable.identifier != stable_obj.identifier) and (stable_obj.machine is True):
                        stable_obj.identifier = new_stable.identifier
                        stable_obj.save()
                        trigger_build(project=project, version=stable_obj)
                else:
                    version = project.versions.create(slug='stable', verbose_name='stable', machine=True, type=new_stable.type, active=True, identifier=new_stable.identifier)
                    trigger_build(project=project, version=version)
        except:
            log.exception("Supported Versions Failure", exc_info=True)

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
        return self.model.objects.public(self.request.user)

    @decorators.link()
    def downloads(self, request, **kwargs):
        version = get_object_or_404(Version.objects.public(self.request.user), pk=kwargs['pk'])
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
        return self.model.objects.public(self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = EmailHook

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        return self.model.objects.public(self.request.user)
