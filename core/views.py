from django.conf import settings
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_view_exempt
from django.views.static import serve

import json
import os
import re

from projects.models import Project
from projects.tasks import update_docs
from projects.utils import find_file
from watching.models import PageView
from bookmarks.models import Bookmark


def homepage(request):
    projs = Project.objects.live()[:5]
    updated = PageView.objects.all()[:5]
    marks = Bookmark.objects.all()[:5]
    return render_to_response('homepage.html',
                              {'project_list': projs,
                               'bookmark_list': marks,
                               'updated_list': updated},
                context_instance=RequestContext(request))

@csrf_view_exempt
def github_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    ghetto_url = url.replace('http://', '')
    project = Project.objects.filter(repo__contains=ghetto_url)[0]
    update_docs.delay(pk=project.pk)
    return HttpResponse('Build Started')

@csrf_view_exempt
def generic_build(request, pk):
    update_docs.delay(pk=pk)
    return HttpResponse('Build Started')

def serve_docs(request, username, project_slug, filename):
    proj = Project.objects.get(slug=project_slug, user__username=username)
    if not filename:
        filename = "index.html"
    filename = filename.rstrip('/')
    if 'html' in filename:
        try:
            proj.full_html_path
        except AttributeError:
            return render_to_response('404.html', {'project': proj},
                    context_instance=RequestContext(request))

        pageview, created = PageView.objects.get_or_create(project=proj, url=filename)
        if not created:
            pageview.count = F('count') + 1
            pageview.save()
    return serve(request, filename, proj.full_html_path)

def render_header(request):
    # try to deconstruct the request url to find the user and project
    project = None

    path_info = request.META['PATH_INFO']
    path_match = re.match('/projects/([-\w]+)/([-\w]+)/', path_info)
    if path_match:
        user, project_slug = path_match.groups()
        try:
            project = Project.objects.get(
                user__username=user,
                slug=project_slug
            )
        except Project.DoesNotExist:
            pass
    context = { 'project': project,
            'do_bookmarking': True,
            'include_render': True,
            }

    if request.user.is_authenticated():
        try:
            mark = Bookmark.objects.get(user=request.user, url=path_info)
            context['has_bookmark'] = True
        except Bookmark.DoesNotExist:
            pass
    return render_to_response('core/header.html', context,
                context_instance=RequestContext(request))

def server_error(request, template_name='500.html'):
    return render_to_response(template_name,
        context_instance = RequestContext(request)
    )

