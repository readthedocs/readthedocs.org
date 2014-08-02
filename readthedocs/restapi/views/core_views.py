from rest_framework import decorators, permissions, status
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from core.utils import clean_url, cname_to_slug
from projects.models import Project

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


