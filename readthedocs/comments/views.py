import json

from .backend import DjangoStorage
from .session import UnsafeSessionAuthentication
from django.shortcuts import render_to_response
from django.template import RequestContext
from sphinx.websupport import WebSupport

from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, JSONPRenderer, BrowsableAPIRenderer
from rest_framework.decorators import (
    api_view, 
    authentication_classes,
    permission_classes, 
    renderer_classes,
    )
from rest_framework.response import Response

storage = DjangoStorage()

support = WebSupport(
        srcdir='/Users/eric/projects/readthedocs.org/docs',
        builddir='/Users/eric/projects/readthedocs.org/docs/_build/websupport',
        datadir='/Users/eric/projects/readthedocs.org/docs/_build/websupport/data',
        storage=storage,
        docroot='websupport',
    )


########
# called by javascript
########

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
@renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def get_comments(request):
    username = None
    node_id = request.GET.get('node', '')
    data = support.get_data(node_id, username=username)
    if data:
        return Response(data)
    else:
        return Response(status=404)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
@renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def get_options(request):
    return Response(support.base_comment_opts)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
@renderer_classes((JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def get_metadata(request):
    """
    Check for get_metadata
    GET: page
    """
    document = request.GET.get('page', '')
    return Response(storage.get_metadata(docname=document))

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([UnsafeSessionAuthentication])
@renderer_classes((JSONRenderer, JSONPRenderer))
def add_comment(request):
    parent_id = request.POST.get('parent', '')
    node_id = request.POST.get('node', '')
    text = request.POST.get('text', '')
    proposal = request.POST.get('proposal', '')
    username = None
    comment = support.add_comment(text=text, node_id=node_id,
                                  parent_id=parent_id,
                                  username=username, proposal=proposal) 
    return Response(comment)


#######
# Normal Views
#######

def build(request):
    support.build()

def serve_file(request, file):
    document = support.get_document(file)

    return render_to_response('doc.html',
                              {'document': document},
                              context_instance=RequestContext(request))

######
# Called by Builder
######

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def has_node(request):
    """
    Checks to see if a node exists.
    GET: node_id - The node's ID to check
    """
    node_id = request.GET.get('node_id', '')
    exists = storage.has_node(node_id)
    return Response({'exists': exists})

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([UnsafeSessionAuthentication])
@renderer_classes((JSONRenderer,))
def add_node(request):
    post_data = request.DATA
    document = post_data.get('document', '')
    id = post_data.get('id', '')
    source = post_data.get('source', '')
    project = post_data.get('project', '')
    version = post_data.get('version', '')
    created = storage.add_node(id, document, source, project=project, version=version)
    return Response({'created': created})
