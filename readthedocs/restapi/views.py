from django.shortcuts import get_object_or_404

from distlib.version import UnsupportedVersionError
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import link
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from betterversion.better import version_windows, BetterVersion 
from projects.models import Project, EmailHook

from .permissions import RelatedProjectIsOwner

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    model = Project

    @link()
    def valid_versions(self, request, **kwargs):
        """
        Maintain state of versions that are wanted.
        """
        project = get_object_or_404(Project, pk=kwargs['pk'])
        if not project.num_major or not project.num_minor or not project.num_point:
            return Response({'error': 'Project does not support point version control.'})
        versions = []
        for ver in project.versions.all():
            try:
                versions.append(BetterVersion(ver.verbose_name))
            except UnsupportedVersionError:
                # Probably a branch
                pass
        active_versions = version_windows(
            versions, 
            major=project.num_major, 
            minor=project.num_minor, 
            point=project.num_point,
            flat=True,
        )
        version_strings = [v._string for v in active_versions]
        # Disable making old versions inactive for now.
        #project.versions.exclude(verbose_name__in=version_strings).update(active=False)
        project.versions.filter(verbose_name__in=version_strings).update(active=True)
        return Response({
            'flat': version_strings,
            })

    @link()
    def translations(self, request, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        ret_val = []
        for translation in project.translations.all():
            ret_val['slug'] = translation.slug
            ret_val['language'] = translation.language
        return Response({'translations': ret_val})

class NotificationViewSet(viewsets.ModelViewSet):
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
