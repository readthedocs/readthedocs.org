from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

import json
import requests

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from core.utils import clean_url, cname_to_slug
from builds.models import Version
from projects.models import Project
from core.templatetags.core_tags import make_document_url


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
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
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def docurl(request):
    """
    Get the url that a slug resolves to.

    Example::

        GET https://readthedocs.org/api/v2/docurl/?project=requests&version=latest&doc=index

    """
    project = request.GET.get('project')
    version = request.GET.get('version', 'latest')
    doc = request.GET.get('doc', 'index')

    project = get_object_or_404(Project, slug=project)
    version = get_object_or_404(Version.objects.public(request.user, project=project, only_active=False), slug=version)
    return Response({
        'url': make_document_url(project=project, version=version.slug, page=doc)
    })


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def embed(request):
    """
    Embed a section of content from any Read the Docs page.

    Returns headers and content that matches the queried section.

    ### Arguments

        * project (requied)
        * doc (required)
        * version (default latest)
        * section

    ### Example

        GET https://readthedocs.org/api/v2/embed/?project=requests&doc=index&section=User%20Guide

    # Current Request
    """
    project = request.GET.get('project')
    version = request.GET.get('version', 'latest')
    doc = request.GET.get('doc')
    section = request.GET.get('section')

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
