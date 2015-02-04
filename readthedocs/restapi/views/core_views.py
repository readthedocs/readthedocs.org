from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

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


