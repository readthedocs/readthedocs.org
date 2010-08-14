from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_view_exempt

import json

from projects.models import Project
from projects.tasks import update_docs
from projects.utils import find_file


@csrf_view_exempt
def github_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    project = Project.objects.get(github_repo=url)
    update_docs.delay(slug=project.slug)
    return HttpResponse('Build Started')

def serve_docs(request, username, project_slug, filename):
    proj = Project.objects.get(slug=project_slug, user__username=username)
    if not filename:
        filename = "index.html"
    filename = filename.rstrip('/')
    return serve(request, filename, proj.full_html_path)
