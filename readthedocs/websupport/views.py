import json

from .backend import DjangoStorage
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from sphinx.websupport import WebSupport

storage = DjangoStorage()

support = WebSupport(
        srcdir='/Users/eric/projects/readthedocs.org/docs',
        builddir='/Users/eric/projects/readthedocs.org/docs/_build/websupport',
        datadir='/Users/eric/projects/readthedocs.org/docs/_build/websupport/data',
        storage=storage,
        docroot='websupport',
    )


def jsonify(obj):
    return HttpResponse(json.dumps(obj), mimetype='text/javascript')

def build(request):
    support.build()

def serve_file(request, file):
    document = support.get_document(file)

    return render_to_response('doc.html',
                              {'document': document},
                              context_instance=RequestContext(request))

@csrf_exempt
def add_comment(request):
    parent_id = request.POST.get('parent', '')
    node_id = request.POST.get('node', '')
    text = request.POST.get('text', '')
    proposal = request.POST.get('proposal', '')
    username = None
    comment = support.add_comment(text=text, node_id=node_id,
                                  parent_id=parent_id,
                                  username=username, proposal=proposal)
    return jsonify(comment)

def get_comments(request):
    username = None
    node_id = request.GET.get('node', '')
    data = support.get_data(node_id, username=username)
    return jsonify(data)


def get_metadata(request):
    document = request.GET.get('document', '')
    return jsonify(storage.get_metadata(docname=document))

def get_options(request):
    document = request.GET.get('document', '')
    return jsonify(support.base_comment_opts)
