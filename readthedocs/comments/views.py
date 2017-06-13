"""Views for comments app."""

from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
    detail_route
)
from rest_framework.exceptions import ParseError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from sphinx.websupport import WebSupport

from readthedocs.comments.models import (
    DocumentComment, DocumentNode, NodeSnapshot, DocumentCommentSerializer,
    DocumentNodeSerializer, ModerationActionSerializer)
from readthedocs.projects.models import Project
from readthedocs.restapi.permissions import CommentModeratorOrReadOnly

from .backend import DjangoStorage
from .session import UnsafeSessionAuthentication
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
@renderer_classes((JSONRenderer,))
def get_options(request):  # pylint: disable=unused-argument
    base_opts = support.base_comment_opts
    base_opts['addCommentURL'] = '/api/v2/comments/'
    base_opts['getCommentsURL'] = '/api/v2/comments/'
    return Response(base_opts)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
@renderer_classes((JSONRenderer,))
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
@renderer_classes((JSONRenderer,))
def attach_comment(request):
    comment_id = request.POST.get('comment', '')
    comment = DocumentComment.objects.get(pk=comment_id)

    node_id = request.POST.get('node', '')
    snapshot = NodeSnapshot.objects.get(hash=node_id)
    comment.node = snapshot.node

    serialized_comment = DocumentCommentSerializer(comment)
    return Response(serialized_comment.data)


#######
# Normal Views
#######

def build(request):  # pylint: disable=unused-argument
    support.build()


def serve_file(request, file):  # pylint: disable=redefined-builtin
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
    post_data = request.data
    project = Project.objects.get(slug=post_data['project'])
    page = post_data.get('document', '')
    node_hash = post_data.get('id', '')
    version = post_data.get('version', '')
    commit = post_data.get('commit', '')
    project.add_node(node_hash, page, version=version, commit=commit)
    return Response()


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([UnsafeSessionAuthentication])
@renderer_classes((JSONRenderer,))
def update_node(request):
    post_data = request.data
    try:
        old_hash = post_data['old_hash']
        new_hash = post_data['new_hash']
        commit = post_data['commit']
        project = post_data['project']
        version = post_data['version']
        page = post_data['page']

        node = DocumentNode.objects.from_hash(
            node_hash=old_hash, project_slug=project, version_slug=version,
            page=page)

        node.update_hash(new_hash, commit)
        return Response(DocumentNodeSerializer(node).data)
    except KeyError:
        return Response("You must include new_hash and commit in POST payload to this view.",
                        status.HTTP_400_BAD_REQUEST)


class CommentViewSet(ModelViewSet):

    """Viewset for Comment model."""

    serializer_class = DocumentCommentSerializer
    permission_classes = [CommentModeratorOrReadOnly, permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qp = self.request.query_params
        if qp.get('node'):
            try:
                node = DocumentNode.objects.from_hash(version_slug=qp['version'],
                                                      page=qp['document_page'],
                                                      node_hash=qp['node'],
                                                      project_slug=qp['project'])
                queryset = DocumentComment.objects.filter(node=node)

            except KeyError:
                raise ParseError(
                    'To get comments by node, you must also provide page, '
                    'version, and project.')
            except DocumentNode.DoesNotExist:
                queryset = DocumentComment.objects.none()
        elif qp.get('project'):
            queryset = DocumentComment.objects.filter(node__project__slug=qp['project'])

        else:
            queryset = DocumentComment.objects.all()
        return queryset

    @method_decorator(login_required)
    def create(self, request, *args, **kwargs):
        project = Project.objects.get(slug=request.data['project'])
        comment = project.add_comment(version_slug=request.data['version'],
                                      page=request.data['document_page'],
                                      content_hash=request.data['node'],
                                      commit=request.data['commit'],
                                      user=request.user,
                                      text=request.data['text'])

        serializer = self.get_serializer(comment)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['put'])
    def moderate(self, request, pk):  # pylint: disable=unused-argument
        comment = self.get_object()
        decision = request.data['decision']
        moderation_action = comment.moderate(request.user, decision)

        return Response(ModerationActionSerializer(moderation_action).data)
