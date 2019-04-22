# -*- coding: utf-8 -*-

"""Utility endpoints relating to canonical urls, embedded content, etc."""

from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.core.templatetags.core_tags import make_document_url
from readthedocs.projects.models import Project


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def docurl(request):
    """
    Get the url that a slug resolves to.

    Example::

        GET https://readthedocs.org/api/v2/docurl/?project=requests&version=latest&doc=index
    """
    project = request.GET.get('project')
    version = request.GET.get('version', LATEST)
    doc = request.GET.get('doc', 'index')
    if project is None:
        return Response(
            {'error': 'Need project and doc'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = get_object_or_404(Project, slug=project)
    version = get_object_or_404(
        Version.objects
        .public(request.user, project=project, only_active=False),
        slug=version,
    )
    return Response({
        'url': make_document_url(
            project=project,
            version=version.slug,
            page=doc,
        ),
    })
