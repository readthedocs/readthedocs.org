"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.
"""

from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import F, Max
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponsePermanentRedirect, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_view_exempt
from django.views.static import serve
from django.views.generic import TemplateView

from haystack.views import FacetedSearchView
from haystack.query import SearchQuerySet, EmptySearchQuerySet

from core.forms import FacetedSearchForm
from projects.models import Project, ImportedFile, ProjectRelationship
from projects.tasks import update_docs, remove_dir
from builds.models import Version

import json
import mimetypes
import os
import logging

log = logging.getLogger(__name__)

def homepage(request):
    #latest_projects = Project.objects.filter(builds__isnull=False).annotate(max_date=Max('builds__date')).order_by('-max_date')[:10]
    latest_projects = Project.objects.order_by('-modified_date')[:10]
    featured = Project.objects.filter(featured=True)

    return render_to_response('homepage.html',
                              {'project_list': latest_projects,
                               'featured_list': featured,
                               #'updated_list': updated
                               },
                context_instance=RequestContext(request))

def random_page(request, project=None):
    if project:
        return HttpResponseRedirect(ImportedFile.objects.filter(project__slug=project).order_by('?')[0].get_absolute_url())
    return HttpResponseRedirect(ImportedFile.objects.order_by('?')[0].get_absolute_url())

@csrf_view_exempt
def wipe_version(request, project_slug, version_slug):
    version = get_object_or_404(Version, project__slug=project_slug, slug=version_slug)
    if request.user not in version.project.users.all():
        raise Http404("You must own this project to wipe it.")
    del_dir = version.project.checkout_path(version.slug)
    if request.method == 'POST' and del_dir:
        remove_dir.delay(del_dir)
        return render_to_response('wipe_version.html', {
                    'del_dir': del_dir,
                    'deleted': True,
                },
                context_instance=RequestContext(request))
    return render_to_response('wipe_version.html', {
            'del_dir': del_dir,
        },
        context_instance=RequestContext(request))

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
        branch = obj['ref'].replace('refs/heads/', '')
        log.info("(Github Build) %s:%s" % (ghetto_url, branch))
        version_pk = None
        version_slug = branch
        try:
            projects = Project.objects.filter(repo__contains=ghetto_url)
            for project in projects:
                version = project.version_from_branch_name(branch)
                if version:
                    log.info("(Github Build) Processing %s:%s" % (project.slug, version.slug))
                    default = project.default_branch or project.vcs_repo().fallback_branch
                    if branch == default:
                        #Shortcircuit versions that are default
                        #These will build at "latest", and thus won't be active
                        version = project.versions.get(slug='latest')
                        version_pk = version.pk
                        version_slug = version.slug
                        log.info("(Github Build) Building %s:%s" % (project.slug, version.slug))
                    elif version in project.versions.exclude(active=True):
                        log.info("(Github Build) Not building %s" % version.slug)
                        return HttpResponseNotFound('Not Building: %s' % branch)
                    else:
                        version_pk = version.pk
                        version_slug = version.slug
                        log.info("(Github Build) Building %s:%s" % (project.slug, version.slug))
                else:
                    version_slug = 'latest'
                    branch = 'latest'
                    log.info("(Github Build) Building %s:latest" % project.slug)
                #version_pk being None means it will use "latest"
                update_docs.delay(pk=project.pk, version_pk=version_pk, force=True)
            return HttpResponse('Build Started: %s' % version_slug)
        except Exception, e:
            log.error("(Github Build) Failed: %s:%s" % (name, e))
            #handle new repos
            project = Project.objects.filter(repo__contains=ghetto_url)
            if not len(project):
                project = Project.objects.filter(name__icontains=name)
                if len(project):
                    #Bail if we think this thing exists
                    return HttpResponseNotFound('Build Failed')
            #create project
            try:
                email = obj['repository']['owner']['email']
                desc = obj['repository']['description']
                homepage = obj['repository']['homepage']
                repo = obj['repository']['url']
                user = User.objects.get(email=email)
                proj = Project.objects.create(
                    name=name,
                    description=desc,
                    project_url=homepage,
                    repo=repo,
                )
                proj.users.add(user)
                log.error("Created new project %s" % (proj))
            except Exception, e:
                log.error("Error creating new project %s: %s" % (name, e))
                return HttpResponseNotFound('Build Failed')

            return HttpResponseNotFound('Build Failed')
    else:
        return render_to_response('post_commit.html', {},
                context_instance=RequestContext(request))

@csrf_view_exempt
def bitbucket_build(request):
    if request.method == 'POST':
        obj = json.loads(request.POST['payload'])
        rep = obj['repository']
        name = rep['name']
        url = "%s%s" % ("bitbucket.org",  rep['absolute_url'].rstrip('/'))
        log.info("(Bitbucket Build) %s" % (url))
        try:
            project = Project.objects.filter(repo__contains=url)[0]
            update_docs.delay(pk=project.pk, force=True)
            return HttpResponse('Build Started')
        except Exception, e:
            log.error("(Github Build) Failed: %s:%s" % (name, e))
            return HttpResponseNotFound('Build Failed')
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
            update_docs.delay(pk=pk, version_pk=version.pk, force=True)
        else:
            update_docs.delay(pk=pk, force=True)
        #return HttpResponse('Build Started')
        return render_to_response('post_commit.html', context,
                context_instance=RequestContext(request))
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

def subproject_serve_docs(request, project_slug, lang_slug, version_slug, filename=''):
    parent_slug = request.slug
    subproject_qs = ProjectRelationship.objects.filter(parent__slug=parent_slug, child__slug=project_slug)
    if subproject_qs.exists():
        return serve_docs(request, lang_slug, version_slug, filename, project_slug)
    else:
        log.info('Subproject lookup failed: %s:%s' % (project_slug, parent_slug))
        raise Http404("Subproject does not exist")

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
    #This is required because we're forming the filenames outselves instead of letting the web server do it.
    elif proj.documentation_type == 'sphinx_htmldir' and "_static" not in filename and "_images" not in filename and "html" not in filename and not "inv" in filename:
        filename += "index.html"
    else:
        filename = filename.rstrip('/')
    basepath = os.path.join(proj.rtd_build_path(version_slug), lang_slug)
    log.info('Serving %s for %s' % (filename, proj))
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
                                             lang_slug,
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


class SearchView(TemplateView):

    template_name = "search/base_facet.html"
    results = EmptySearchQuerySet()
    form_class = FacetedSearchForm
    form = None
    query = ''
    selected_facets = None
    selected_facets_list = None

    def get_context_data(self, request, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['request'] = self.request
        context['facets'] = self.results.facet_counts() # causes solr request #1
        context['form'] = self.form
        context['query'] = self.query
        context['selected_facets'] = '&'.join(self.selected_facets) if self.selected_facets else ''
        context['selected_facets_list'] = self.selected_facets_list
        context['results'] = self.results
        context['count'] = len(self.results) # causes solr request #2
        return context
 
    def get(self, request, **kwargs):
        """
        Performing the search causes three requests to be sent to Solr.
            1. For the facets
            2. For the count (unavoidable, as pagination will cause this anyay)
            3. For the results
        """
        self.request = request
        self.form = self.build_form()
        self.selected_facets = self.get_selected_facets()
        self.selected_facets_list = self.get_selected_facets_list()
        self.query = self.get_query()
        if self.form.is_valid():
            self.results = self.get_results()
        context = self.get_context_data(request, **kwargs)

        # For returning results partials for javascript
        if request.is_ajax() or request.GET.get('ajax'):
            self.template_name = 'search/faceted_results.html'

        return self.render_to_response(context)

    def build_form(self):
        """
        Instantiates the form the class should use to process the search query.
        """
        data = self.request.GET if len(self.request.GET) else None
        return self.form_class(data, facets=('project',))

    def get_selected_facets_list(self):
        return [tuple(s.split(':')) for s in self.selected_facets if s]

    def get_selected_facets(self):
        """
        Returns the a list of facetname:value strings

        e.g. [u'project_exact:Read The Docs', u'author_exact:Eric Holscher']
        """
        return self.request.GET.getlist('selected_facets')

    def get_query(self):
        """
        Returns the query provided by the user.
        Returns an empty string if the query is invalid.
        """
        return self.request.GET.get('q')

    def get_results(self):
        """
        Fetches the results via the form.
        """
        return self.form.search()
