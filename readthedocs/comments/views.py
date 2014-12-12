import json

from .backend import DjangoStorage
from .session import UnsafeSessionAuthentication
from django.shortcuts import render_to_response
from django.template import RequestContext
from sphinx.websupport import WebSupport

from rest_framework import permissions, status
from rest_framework.renderers import JSONRenderer, JSONPRenderer, BrowsableAPIRenderer
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.response import Response
from comments.models import DocumentComment, DocumentNode, NodeSnapshot, DocumentCommentSerializer,\
    DocumentNodeSerializer
from projects.models import Project
from django.http.response import HttpResponseRedirect

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
    try:
        hash = request.POST['node']
        commit = request.POST['commit']
    except KeyError:
        return Response("You must provide a node (hash) and initial commit.",
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        snapshot = NodeSnapshot.objects.get(hash=hash)
        node = snapshot.node
        created = False
    except NodeSnapshot.DoesNotExist:
        project = Project.objects.get(slug=request.DATA['project'])
        version = project.versions.get(slug=request.DATA['version'])
        node = DocumentNode.objects.create(project=project,
                                           version=version,
                                           hash=hash,
                                           commit=commit,
                                           )
        created = True

    text = request.POST.get('text', '')
    comment = DocumentComment.objects.create(text=text,
                                             node=node,
                                             user=request.user)

    serialized_comment = DocumentCommentSerializer(comment)
    response_dict = serialized_comment.data
    response_dict['created'] = created

    return Response(serialized_comment.data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([UnsafeSessionAuthentication])
@renderer_classes((JSONRenderer, JSONPRenderer))
def attach_comment(request):
    comment_id = request.POST.get('comment', '')
    comment = DocumentComment.objects.get(pk=comment_id)

    node_id = request.POST.get('node', '')
    snapshot = NodeSnapshot.objects.get(hash=node_id)
    comment.node = snapshot.node

    serialized_comment = DocumentCommentSerializer(comment)
    serialized_comment.data
    return Response(serialized_comment.data)


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
    page = post_data.get('document', '')
    id = post_data.get('id', '')
    project = post_data.get('project', '')
    version = post_data.get('version', '')
    commit = post_data.get('commit', '')
    created = storage.add_node(id, page, project=project, version=version, commit=commit)
    return Response({'created': created})


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([UnsafeSessionAuthentication])
@renderer_classes((JSONRenderer,))
def update_node(request):
    post_data = request.DATA
    try:
        old_hash = post_data['old_hash']
        new_hash = post_data['new_hash']
        commit = post_data['commit']
        node = DocumentNode.objects.from_hash(hash=old_hash)
        node.update_hash(new_hash, commit)
        return Response(DocumentNodeSerializer(node).data)
    except KeyError:
        return Response("You must include new_hash and commit in POST payload to this view.",
                        status.HTTP_400_BAD_REQUEST)


def moderate_comment(request, comment_id):
    post_data = request.DATA
    comment = DocumentComment.objects.get(id=comment_id)

    decision = post_data['decision']
    comment.moderate(request.user, decision)
    return HttpResponseRedirect(comment.node.project.get_absolute_url())

