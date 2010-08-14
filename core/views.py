from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_view_exempt

import json
import os

from projects.models import Project
from projects.tasks import update_docs
from projects.utils import get_project_path, find_file


@csrf_view_exempt
def github_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    project = Project.objects.get(github_repo=url)
    update_docs.delay(slug=project.slug)
    return HttpResponse('Build Started')

def serve_docs(request, username, project_slug, filename="index.html"):
    proj = Project.objects.get(slug=project_slug, user__username=username)
    project = proj.slug
    path = get_project_path(proj)
    filename = filename.rstrip('/')

    doc_base = os.path.join(path, project)
    for possible_path in ['docs', 'doc']:
        if os.path.exists( os.path.join(doc_base, '%s/build/html' % possible_path)):
            final_path = os.path.join(doc_base, '%s/build/html' % possible_path) 
        elif os.path.exists( os.path.join(doc_base, '%s/_build/html' % possible_path)):
            final_path = os.path.join(doc_base, '%s/_build/html' % possible_path) 
        elif os.path.exists( os.path.join(doc_base, '%s/.build/html' % possible_path)):
            final_path = os.path.join(doc_base, '%s/.build/html' % possible_path) 
    return serve(request, filename, final_path)

