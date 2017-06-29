"""Utility endpoints relating to canonical urls, embedded content, etc."""

from __future__ import absolute_import

from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

import json
import requests

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from readthedocs.core.utils import clean_url, cname_to_slug
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.core.templatetags.core_tags import make_document_url


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def cname(request):
    """
    Get the slug that a particular hostname resolves to.

    This is useful for debugging your DNS settings,
    or for getting the backing project name on Read the Docs for a URL.

    Example::

        GET https://readthedocs.org/api/v2/cname/?host=docs.python-requests.org

    This will return information about ``docs.python-requests.org``
    """
    host = request.GET.get('host')
    if not host:
        return Response({'error': 'host GET arg required'}, status=status.HTTP_400_BAD_REQUEST)
    host = clean_url(host)
    slug = cname_to_slug(host)
    return Response({
        'host': host,
        'slug': slug,
    })


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
        return Response({'error': 'Need project and doc'}, status=status.HTTP_400_BAD_REQUEST)

    project = get_object_or_404(Project, slug=project)
    version = get_object_or_404(
        Version.objects.public(request.user, project=project, only_active=False),
        slug=version)
    return Response({
        'url': make_document_url(project=project, version=version.slug, page=doc)
    })


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def embed(request):
    """
    Embed a section of content from any Read the Docs page.

    Returns headers and content that matches the queried section.

    ### Arguments

        * project (required)
        * doc (required)
        * version (default latest)
        * section

    ### Example

        GET https://readthedocs.org/api/v2/embed/?project=requests&doc=index&section=User%20Guide

    # Current Request
    """
    project = request.GET.get('project')
    version = request.GET.get('version', LATEST)
    doc = request.GET.get('doc')
    section = request.GET.get('section')

    if project is None or doc is None:
        return Response({'error': 'Need project and doc'}, status=status.HTTP_400_BAD_REQUEST)

    embed_cache = cache.get('embed:%s' % project)
    if embed_cache:
        embed = json.loads(embed_cache)
    else:
        try:
            resp = requests.get(
                '{host}/api/v1/embed/'.format(host=settings.GROK_API_HOST),
                params={'project': project, 'version': version, 'doc': doc, 'section': section}
            )
            embed = resp.json()
            cache.set('embed:%s' % project, resp.content, 1800)
        except Exception as e:
            return Response({'error': '%s' % e.msg}, status=status.HTTP_400_BAD_REQUEST)

    return Response(embed)
