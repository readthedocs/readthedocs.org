"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.
"""

from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db.models import F, Max
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponsePermanentRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_view_exempt
from django.views.static import serve
from projects.models import Project
from projects.tasks import update_docs
from watching.models import PageView
import json
import os
import re




def homepage(request):
    projs = Project.objects.select_related().filter(builds__isnull=False).annotate(max_date=Max('builds__date')).order_by('-max_date')[:10]
    featured = Project.objects.select_related().filter(featured=True)
    updated = PageView.objects.select_related().all()[:10]
    return render_to_response('homepage.html',
                              {'project_list': projs,
                               'featured_list': featured,
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
        return render_to_response('post_commit.html', {},
                context_instance=RequestContext(request))

@csrf_view_exempt
def bitbucket_build(request):
    if request.method == 'POST':
        obj = json.loads(request.POST['payload'])
        rep = obj['repository']
        name = rep['name']
        url = "%s%s" % ("bitbucket.org",  rep['absolute_url'])
        try:
            project = Project.objects.filter(repo__contains=url)[0]
            update_docs.delay(pk=project.pk)
            return HttpResponse('Build Started')
        except:
            mail_admins('Build Failure', '%s failed to build via github' % name)
            return HttpResponse('Build Failed')
    else:
        return render_to_response('post_commit.html', {},
                context_instance=RequestContext(request))

@csrf_view_exempt
def generic_build(request, pk):
    project = Project.objects.get(pk=pk)
    context = {'built': False, 'project': project}
    #This should be in the post, but for now it's always built for backwards compat
    update_docs.delay(pk=pk)
    if request.method == 'POST':
        context['built'] = True
    return render_to_response('post_commit.html', context,
            context_instance=RequestContext(request))


def legacy_serve_docs(request, username, project_slug, filename):
    proj = get_object_or_404(Project, slug=project_slug)
    default_version = proj.get_default_version()
    url = reverse(serve_docs, kwargs={
        'project_slug': project_slug,
        'version_slug': default_version,
        'lang_slug': 'en',
        'filename': filename
    })
    return HttpResponsePermanentRedirect(url)


def serve_docs(request, project_slug, lang_slug, version_slug, filename):
    """
    The way that we're serving the documentation.

    This is coming out of Django so that we can do simple page counting, and
    because later we can use Django auth to protect views.

    This could probably be refactored to serve out of nginx if we have more
    time.
    """
    # A bunch of janky redirect logic. This should be the last time.
    proj = get_object_or_404(Project, slug=project_slug)
    default_version = proj.get_default_version()
    if not filename:
        filename = "index.html"
    if version_slug is None:
        url = reverse(serve_docs, kwargs={
            'project_slug': project_slug,
            'version_slug': default_version,
            'lang_slug': 'en',
            'filename': filename
        })
        return HttpResponsePermanentRedirect(url)
    if lang_slug is None:
        url = reverse(serve_docs, kwargs={
            'project_slug': project_slug,
            'version_slug': version_slug if version_slug != 'en' else default_version,
            'lang_slug': 'en',
            'filename': filename
        })
        return HttpResponseRedirect(url)
    valid_version = proj.versions.filter(slug=version_slug).count()
    if not valid_version and version_slug != 'latest' and version_slug != 'en':
        url = reverse(serve_docs, kwargs={
            'project_slug': project_slug,
            'version_slug': default_version,
            'lang_slug': 'en',
            #Filename was part of the version that we caught.
            'filename': os.path.join(version_slug, filename)
        })
        return HttpResponsePermanentRedirect(url)
    filename = filename.rstrip('/')
    basepath = os.path.join(proj.rtd_build_path, version_slug)
    if 'html' in filename:
        try:
            if not os.path.exists(os.path.join(basepath, filename)):
                return render_to_response('404.html', {'project': proj},
                        context_instance=RequestContext(request))
        except AttributeError:
            return render_to_response('404.html', {'project': proj},
                    context_instance=RequestContext(request))

        pageview, created = PageView.objects.get_or_create(project=proj, url=filename)
        if not created:
            pageview.count = F('count') + 1
            pageview.save()
    return serve(request, filename, basepath)

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
