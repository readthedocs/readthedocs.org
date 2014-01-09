import logging

from django.shortcuts import get_object_or_404

from rest_framework import decorators, permissions, viewsets, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from builds.models import Version
from projects.models import Project, EmailHook

from restapi.serializers import ProjectSerializer, VersionSerializer
from restapi.permissions import RelatedProjectIsOwner
import restapi.utils as api_utils

log = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, JSONPRenderer, BrowsableAPIRenderer)
    model = Project

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given project,
        by filtering against a `slug` query parameter in the URL.
        """
        queryset = Project.objects.all()
        slug = self.request.QUERY_PARAMS.get('slug', None)
        if slug is not None:
            queryset = queryset.filter(slug=slug)
        return queryset

    @decorators.link()
    def valid_versions(self, request, **kwargs):
        """
        Maintain state of versions that are wanted.
        """
        project = get_object_or_404(Project, pk=kwargs['pk'])
        if not project.num_major or not project.num_minor or not project.num_point:
            return Response({'error': 'Project does not support point version control'}, status=status.HTTP_400_BAD_REQUEST)
        version_strings = project.supported_versions(flat=True)
        # Disable making old versions inactive for now.
        #project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(verbose_name__in=version_strings).update(active=True)
        return Response({
            'flat': version_strings,
            })

    @decorators.link()
    def translations(self, request, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        queryset = project.translations.all()
        return Response({
            'translations': ProjectSerializer(queryset, many=True).data
        })

    @decorators.link()
    def subprojects(self, request, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        rels = project.subprojects.all()
        children = [rel.child for rel in rels]
        return Response({
            'subprojects': ProjectSerializer(children, many=True).data
        })

    @decorators.action(permission_classes=[permissions.IsAdminUser])
    def sync_versions(self, request, **kwargs):
        """
        Sync the version data in the repo (on the build server) with what we have in the database.

        Returns the identifiers for the versions that have been deleted.
        """
        project = get_object_or_404(Project, pk=kwargs['pk'])
        try:
            data = request.DATA
            added_versions = set()
            if 'tags' in data:
                ret_set = api_utils.sync_versions(project=project, versions=data['tags'], type='tags')
                added_versions.update(ret_set)
            if 'branches' in data:
                ret_set = api_utils.sync_versions(project=project, versions=data['branches'], type='branches')
                added_versions.update(ret_set)
            deleted_versions = api_utils.delete_versions(project, data)
            return Response({
                'added_versions': added_versions,
                'deleted_versions': deleted_versions,
            })
        except Exception, e:
            log.exception("Sync Versions Error: %s" % e.message)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, RelatedProjectIsOwner)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = EmailHook

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.filter(project__users__in=[user.pk])


class VersionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = VersionSerializer
    model = Version

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given project,
        by filtering against a `project` query parameter in the URL.
        """
        queryset = Version.objects.all()
        project = self.request.QUERY_PARAMS.get('project', None)
        if project is not None:
            queryset = queryset.filter(project__slug=project)
        slug = self.request.QUERY_PARAMS.get('slug', None)
        if slug is not None:
            queryset = queryset.filter(slug=slug)
        return queryset


    @decorators.link()
    def downloads(self, request, **kwargs):
        version = get_object_or_404(Version, pk=kwargs['pk'])
        downloads = version.get_downloads(pretty=True)
        return Response({
            'downloads': downloads
        })
