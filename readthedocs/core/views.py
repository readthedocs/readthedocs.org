"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.
"""

from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.conf import settings
from django.db.models import F, Max
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_view_exempt
from django.views.static import serve

from projects.models import Project
from projects.tasks import update_docs
from watching.models import PageView

import json
import mimetypes
import os


def homepage(request):
    latest_projects = cache.get('latest_projects', None)
    if not latest_projects:
        latest_projects = Project.objects.filter(builds__isnull=False).annotate(max_date=Max('builds__date')).order_by('-max_date')[:10]
        cache.set('latest_projects', list(latest_projects), 30)
    featured = Project.objects.filter(featured=True)
    updated = PageView.objects.all()[:10]
    return render_to_response('homepage.html',
                              {'project_list': latest_projects,
                               'featured_list': featured,
                               'updated_list': updated},
                context_instance=RequestContext(request))

def random_page(request, project=None):
    if project:
        return HttpResponseRedirect(PageView.objects.filter(project__slug=project).order_by('?')[0].get_absolute_url())
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
            update_docs.delay(pk=project.pk, touch=True)
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
            update_docs.delay(pk=project.pk, touch=True)
            return HttpResponse('Build Started')
        except:
            mail_admins('Build Failure', '%s failed to build via bitbucket' % name)
            return HttpResponse('Build Failed')
    else:
        return render_to_response('post_commit.html', {},
                context_instance=RequestContext(request))

@csrf_view_exempt
def generic_build(request, pk):
    project = Project.objects.get(pk=pk)
    context = {'built': False, 'project': project}
    if request.method == 'POST':
        context['built'] = True
        slug = request.POST.get('version_slug', None)
        if slug:
            version = project.versions.get(slug=slug)
            update_docs.delay(pk=pk, version_pk=version.pk, touch=True)
        else:
            update_docs.delay(pk=pk, touch=True)
        return HttpResponse('Build Started')
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


def serve_docs(request, lang_slug, version_slug, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)
    if not version_slug or not lang_slug:
        version_slug = proj.get_default_version()
        url = reverse(serve_docs, kwargs={
            'project_slug': project_slug,
            'version_slug': version_slug,
            'lang_slug': 'en',
            'filename': filename
        })
        return HttpResponseRedirect(url)
    if not filename:
        filename = "index.html"
    elif proj.documentation_type == 'sphinx_htmldir' and "_static" not in filename and "html" not in filename and not "inv" in filename:
        filename += "index.html"
    else:
        filename = filename.rstrip('/')
    basepath = proj.rtd_build_path(version_slug)
    if filename.endswith('html'):
        pageview, created = PageView.objects.get_or_create(project=proj, url=filename)
        if not created:
            pageview.count = F('count') + 1
            pageview.save()
    if not settings.DEBUG:
        fullpath = os.path.join(basepath, filename)
        mimetype, encoding = mimetypes.guess_type(fullpath)
        mimetype = mimetype or 'application/octet-stream'
        response = HttpResponse(mimetype=mimetype)
        if encoding:
            response["Content-Encoding"] = encoding
        try:
            response['X-Accel-Redirect'] = os.path.join('/user_builds',
                                             proj.slug,
                                             'rtd-builds',
                                             version_slug,
                                             filename)
        except UnicodeEncodeError:
            raise Http404

        return response
    else:
        return serve(request, filename, basepath)

def server_error(request, template_name='500.html'):
    """
    A simple 500 handler so we get media
    """
    r = render_to_response(template_name,
        context_instance = RequestContext(request)
    )
    r.status_code = 500
    return r

def server_error_404(request, template_name='404.html'):
    """
    A simple 500 handler so we get media
    """
    r =  render_to_response(template_name,
        context_instance = RequestContext(request)
    )
    r.status_code = 404
    return r
