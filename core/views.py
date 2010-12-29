"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.
"""

from django.core.mail import mail_admins
from django.conf import settings
from django.db.models import F, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
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
    projs = Project.objects.filter(builds__isnull=False).annotate(max_date=Max('builds__date')).order_by('-max_date')[:10]
    updated = PageView.objects.all()[:10]
    marks = Bookmark.objects.all()[:10]
    return render_to_response('homepage.html',
                              {'project_list': projs,
                               'bookmark_list': marks,
                               'updated_list': updated},
                context_instance=RequestContext(request))

def random_page(request):
    return HttpResponseRedirect(PageView.objects.order_by('?')[0].get_absolute_url())

@csrf_view_exempt
def github_build(request):
    """
    A post-commit hook for github.
    """
    if request.method == 'POST':
        obj = json.loads(request.POST['payload'])
        name = obj['repository']['name']
        url = obj['repository']['url']
        ghetto_url = url.replace('http://', '').replace('https://', '')
        try:
            project = Project.objects.filter(repo__contains=ghetto_url)[0]
            update_docs.delay(pk=project.pk)
            return HttpResponse('Build Started')
        except:
            mail_admins('Build Failure', '%s failed to build via github' % name)
            return HttpResponse('Build Failed')
    else:
        return render_to_response('github.html', {},
                context_instance=RequestContext(request))


@csrf_view_exempt
def generic_build(request, pk):
    update_docs.delay(pk=pk)
    return render_to_response('github.html', {},
            context_instance=RequestContext(request))

def serve_docs(request, username, project_slug, filename):
    """
    The way that we're serving the documentation.

    This is coming out of Django so that we can do simple page counting, and
    because later we can use Django auth to protect views.

    This could probably be refactored to serve out of nginx if we have more
    time.
    """
    proj = get_object_or_404(Project, slug=project_slug, user__username=username)
    if not filename:
        filename = "index.html"
    filename = filename.rstrip('/')
    if 'html' in filename:
        try:
            proj.full_html_path
            if not os.path.exists(os.path.join(proj.full_html_path, filename)):
                return render_to_response('404.html', {'project': proj},
                        context_instance=RequestContext(request))
        except AttributeError:
            return render_to_response('404.html', {'project': proj},
                    context_instance=RequestContext(request))

        pageview, created = PageView.objects.get_or_create(project=proj, url=filename)
        if not created:
            pageview.count = F('count') + 1
            pageview.save()
    return serve(request, filename, proj.full_html_path)

def render_header(request):
    """
    This is the ESI backend that renders on top of the sphinx documentation
    that we serve.

    This needs to be Django instead of rendered into the Sphinx Document
    because we need to know who the user is and if they are authenticated and
    such. Later we will provide more "Owner Tools" for users.
    """

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
    """
    A simple 500 handler so we get media
    """
    return render_to_response(template_name,
        context_instance = RequestContext(request)
    )


def server_error_404(request, template_name='404.html'):
    """
    A simple 500 handler so we get media
    """
    return render_to_response(template_name,
        context_instance = RequestContext(request)
    )
