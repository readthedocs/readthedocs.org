"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.

"""

from django.contrib.auth.models import User
from django.core.urlresolvers import NoReverseMatch, reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_view_exempt
from django.views.static import serve
from django.views.generic import TemplateView

from haystack.query import EmptySearchQuerySet
from haystack.query import SearchQuerySet

from builds.models import Build
from builds.models import Version
from core.forms import FacetedSearchForm
from projects.models import Project, ImportedFile, ProjectRelationship
from projects.tasks import update_docs, remove_dir
from projects.utils import highest_version

import json
import mimetypes
import os
import logging
import redis

log = logging.getLogger(__name__)
pc_log = logging.getLogger(__name__+'.post_commit')

class NoProjectException(Exception):
    pass

def homepage(request):
    latest = (Project.objects.public(request.user)
              .order_by('-modified_date')[:10])
    featured = Project.objects.filter(featured=True)

    return render_to_response('homepage.html',
                              {'project_list': latest,
                               'featured_list': featured},
                              context_instance=RequestContext(request))


def random_page(request, project=None):
    imp_file = ImportedFile.objects.order_by('?')
    if project:
        return HttpResponseRedirect((imp_file.filter(project__slug=project)[0]
                                             .get_absolute_url()))
    return HttpResponseRedirect(imp_file[0].get_absolute_url())


def queue_depth(request):
    r = redis.Redis(**settings.REDIS)
    return HttpResponse(r.llen('celery'))


def live_builds(request):
    builds = Build.objects.filter(state='building')[:5]
    WEBSOCKET_HOST = getattr(settings, 'WEBSOCKET_HOST', 'localhost:8088')
    count = builds.count()
    percent = 100
    if count > 1:
        percent = 100 / count
    return render_to_response('all_builds.html',
                              {'builds': builds,
                               'build_percent': percent,
                               'WEBSOCKET_HOST': WEBSOCKET_HOST},
                              context_instance=RequestContext(request))


@csrf_view_exempt
def wipe_version(request, project_slug, version_slug):
    version = get_object_or_404(Version, project__slug=project_slug,
                                slug=version_slug)
    if request.user not in version.project.users.all():
        raise Http404("You must own this project to wipe it.")
    del_dirs = [version.project.checkout_path(version.slug), version.project.venv_path(version.slug)]
    for del_dir in del_dirs:
        remove_dir.delay(del_dir)
    return render_to_response('wipe_version.html',
                              {'del_dir': del_dir},
                              context_instance=RequestContext(request))

def _build_version(project, slug, already_built=()):
    default = project.default_branch or (project.vcs_repo().fallback_branch)
    if slug == default and slug not in already_built:
        # short circuit versions that are default
        # these will build at "latest", and thus won't be
        # active
        version = project.versions.get(slug='latest')
        update_docs.delay(pk=project.pk, version_pk=version.pk, force=True)
        pc_log.info(("(Version build) Building %s:%s"
                  % (project.slug, version.slug)))
        return "latest"
    elif project.versions.exclude(active=True).filter(slug=slug).exists():
        pc_log.info(("(Version build) Not Building %s"% slug))
        return None
    elif slug not in already_built:
        version = project.versions.get(slug=slug)
        update_docs.delay(pk=project.pk, version_pk=version.pk, force=True)
        pc_log.info(("(Version build) Building %s:%s"
                  % (project.slug, version.slug)))
        return slug
    else:
        pc_log.info(("(Version build) Not Building %s"% slug))
        return None

def _build_branches(project, branch_list):
    for branch in branch_list:
        versions = project.versions_from_branch_name(branch)
        to_build = set()
        not_building = set()
        for version in versions:
            pc_log.info(("(Branch Build) Processing %s:%s"
                      % (project.slug, version.slug)))
            ret =  _build_version(project, version.slug, already_built=to_build)
            if ret:
                to_build.add(ret)
            else:
                not_building.add(version.slug)
    return (to_build, not_building)
    

def _build_url(url, branches):
    try:
        projects = Project.objects.filter(repo__contains=url)
        if not projects.count():
            raise NoProjectException()
        for project in projects:
            (to_build, not_building) = _build_branches(project, branches)
        if to_build:
            msg = '(URL Build) Build Started: %s [%s]' % (url, ' '.join(to_build))
            pc_log.info(msg)
            return HttpResponse(msg)
        else:
            msg = '(URL Build) Not Building: %s [%s]' % (url, ' '.join(not_building))
            pc_log.info(msg)
            return HttpResponse(msg)
    except Exception, e:
        if e.__class__ == NoProjectException:
            raise
        msg = "(URL Build) Failed: %s:%s" % (url, e)
        pc_log.error(msg)
        return HttpResponse(msg)


@csrf_view_exempt
def github_build(request):
    """
    A post-commit hook for github.
    """
    if request.method == 'POST':
        obj = json.loads(request.POST['payload'])
        url = obj['repository']['url']
        ghetto_url = url.replace('http://', '').replace('https://', '')
        branch = obj['ref'].replace('refs/heads/', '')
        pc_log.info("(Incoming Github Build) %s [%s]" % (ghetto_url, branch))
        try:
            return _build_url(ghetto_url, [branch])
        except NoProjectException:
            try:
                name = obj['repository']['name']
                desc = obj['repository']['description']
                homepage = obj['repository']['homepage']
                repo = obj['repository']['url']

                email = obj['repository']['owner']['email']
                user = User.objects.get(email=email)

                proj = Project.objects.create(
                    name=name,
                    description=desc,
                    project_url=homepage,
                    repo=repo,
                )
                proj.users.add(user)
                # Version doesn't exist yet, so use classic build method
                update_docs.delay(pk=proj.pk)
                pc_log.info("Created new project %s" % (proj))
            except Exception, e:
                pc_log.error("Error creating new project %s: %s" % (name, e))
                return HttpResponseNotFound('Repo not found')

@csrf_view_exempt
def bitbucket_build(request):
    if request.method == 'POST':
        payload = request.POST.get('payload')
        pc_log.info("(Incoming Bitbucket Build) Raw: %s" % payload)
        if not payload:
            return HttpResponseNotFound('Invalid Request')
        obj = json.loads(payload)
        rep = obj['repository']
        branches = [rec.get('branch', '') for rec in obj['commits']]
        ghetto_url = "%s%s" % ("bitbucket.org",  rep['absolute_url'].rstrip('/'))
        pc_log.info("(Incoming Bitbucket Build) %s [%s]" % (ghetto_url, ' '.join(branches)))
        pc_log.info("(Incoming Bitbucket Build) JSON: \n\n%s\n\n" % obj)
        try:
            return _build_url(ghetto_url, branches)
        except NoProjectException:
            pc_log.error("(Incoming Bitbucket Build) Repo not found:  %s" % ghetto_url)
            return HttpResponseNotFound('Repo not found: %s' % ghetto_url)


@csrf_view_exempt
def generic_build(request, pk=None):
    try:
        project = Project.objects.get(pk=pk)
    # Allow slugs too
    except (Project.DoesNotExist, ValueError):
        project = Project.objects.get(slug=pk)
    if request.method == 'POST':
        slug = request.POST.get('version_slug', None)
        if slug:
            pc_log.info("(Incoming Generic Build) %s [%s]" % (project.slug, slug))
            _build_version(project, slug)
        else:
            pc_log.info("(Incoming Generic Build) %s [%s]" % (project.slug, 'latest'))
            update_docs.delay(pk=pk, force=True)
    return redirect('builds_project_list', project.slug)


def subdomain_handler(request, lang_slug=None, version_slug=None, filename=''):
    """This provides the fall-back routing for subdomain requests.

    This was made primarily to redirect old subdomain's to their version'd
    brothers.

    """
    project = get_object_or_404(Project, slug=request.slug)
    # Don't add index.html for htmldir.
    if not filename and project.documentation_type != 'sphinx_htmldir':
        filename = "index.html"
    if version_slug is None and lang_slug:
        default_version = project.get_default_version()
        url = reverse(serve_docs, kwargs={
            'version_slug': default_version,
            'lang_slug': lang_slug,
            'filename': filename
        })
        return HttpResponseRedirect(url)
    if version_slug is None and lang_slug is None:
        # Handle / on subdomain.
        default_version = project.get_default_version()
        url = reverse(serve_docs, kwargs={
            'version_slug': default_version,
            'lang_slug': project.language,
            'filename': filename
        })
        return HttpResponseRedirect(url)
    if version_slug and lang_slug is None:
        # Handle /version/ on subdomain.
        aliases = project.aliases.filter(from_slug=version_slug)
        # Handle Aliases.
        if aliases.count():
            if aliases[0].largest:
                highest_ver = highest_version(project.versions.filter(
                    slug__contains=version_slug, active=True))
                version_slug = highest_ver[0].slug
            else:
                version_slug = aliases[0].to_slug
            url = reverse(serve_docs, kwargs={
                'version_slug': version_slug,
                'lang_slug': project.language,
                'filename': filename
            })
        else:
            try:
                url = reverse(serve_docs, kwargs={
                    'version_slug': version_slug,
                    'lang_slug': project.language,
                    'filename': filename
                })
            except NoReverseMatch:
                raise Http404
        return HttpResponseRedirect(url)
    # Serve normal docs
    return serve_docs(request=request,
                      project_slug=project.slug,
                      lang_slug=lang_slug,
                      version_slug=version_slug,
                      filename=filename)

def subproject_list(request):
    project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)
    subprojects = [rel.child for rel in proj.subprojects.all()]
    return render_to_response(
        'projects/project_list.html',
        {'project_list': subprojects},
        context_instance=RequestContext(request)
    )

def subproject_serve_docs(request, project_slug, lang_slug=None,
                          version_slug=None, filename=''):
    parent_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)
    subproject_qs = ProjectRelationship.objects.filter(
        parent__slug=parent_slug, child__slug=project_slug)
    if lang_slug is None or version_slug is None:
        # Handle /
        version_slug = proj.get_default_version()
        url = reverse('subproject_docs_detail', kwargs={
            'project_slug': project_slug,
            'version_slug': version_slug,
            'lang_slug': proj.language,
            'filename': filename
        })
        return HttpResponseRedirect(url)

    if subproject_qs.exists():
        return serve_docs(request, lang_slug, version_slug, filename,
                          project_slug)
    else:
        log.info('Subproject lookup failed: %s:%s' % (project_slug,
                                                      parent_slug))
        raise Http404("Subproject does not exist")

def default_docs_kwargs(request, project_slug=None):
    """
    Return kwargs used to reverse lookup a project's default docs URL.

    Determining which URL to redirect to is done based on the kwargs
    passed to reverse(serve_docs, kwargs).  This function populates
    kwargs for the default docs for a project, and sets appropriate keys
    depending on whether request is for a subdomain URL, or a non-subdomain
    URL.

    """
    # If project_slug isn't in URL pattern, it's set in subdomain
    # middleware as request.slug.
    if project_slug is None:
        proj = get_object_or_404(Project, slug=request.slug)
    else:
        proj = get_object_or_404(Project, slug=project_slug)
    version_slug = proj.get_default_version()
    kwargs = {
        'project_slug': project_slug,
        'version_slug': version_slug,
        'lang_slug': proj.language,
        'filename': ''
    }
    # Don't include project_slug for subdomains.
    # That's how reverse(serve_docs, ...) differentiates subdomain
    # views from non-subdomain views.
    if project_slug is None:
        del kwargs['project_slug']
    return kwargs

def redirect_lang_slug(request, lang_slug, project_slug=None):
    """Redirect /en/ to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['lang_slug'] = lang_slug
    url = reverse(serve_docs, kwargs=kwargs)
    return HttpResponseRedirect(url)

def redirect_version_slug(request, version_slug, project_slug=None):
    """Redirect /latest/ to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['version_slug'] = version_slug
    url = reverse(serve_docs, kwargs=kwargs)
    return HttpResponseRedirect(url)

def redirect_project_slug(request, project_slug=None):
    """Redirect / to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    url = reverse(serve_docs, kwargs=kwargs)
    return HttpResponseRedirect(url)

def serve_docs(request, lang_slug, version_slug, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)

    # Redirects
    must_redirect = False
    if version_slug and not lang_slug:
        lang_slug = proj.language
        must_redirect = True
    elif lang_slug and not version_slug:
        version_slug = proj.get_default_version()
        must_redirect = True
    elif not version_slug and not lang_slug:
        lang_slug = proj.language
        version_slug = proj.get_default_version()
        must_redirect = True

    if must_redirect:
        url = reverse(serve_docs, kwargs={
            'project_slug': project_slug,
            'version_slug': version_slug,
            'lang_slug': lang_slug,
            'filename': filename
        })
        return HttpResponseRedirect(url)

    ver = get_object_or_404(Version, project__slug=project_slug,
                            slug=version_slug)
    # Auth checks
    if ver not in proj.versions.public(request.user, proj):
        res = HttpResponse("You don't have access to this version.")
        res.status_code = 401
        return res

    # Normal handling

    if not filename:
        filename = "index.html"
    # This is required because we're forming the filenames outselves instead of
    # letting the web server do it.
    elif (proj.documentation_type == 'sphinx_htmldir'
          and "_static" not in filename
          and "_images" not in filename
          and "html" not in filename
          and not "inv" in filename):
        filename += "index.html"
    else:
        filename = filename.rstrip('/')
    # Use the old paths if we're on our old location.
    # Otherwise use the new language symlinks.
    # This can be removed once we have 'en' symlinks for every project.
    if lang_slug == proj.language:
        basepath = proj.rtd_build_path(version_slug)
    else:
        basepath = proj.translations_path(lang_slug)
        basepath = os.path.join(basepath, version_slug)
    log.info('Serving %s for %s' % (filename, proj))
    if not settings.DEBUG:
        fullpath = os.path.join(basepath, filename)
        mimetype, encoding = mimetypes.guess_type(fullpath)
        mimetype = mimetype or 'application/octet-stream'
        response = HttpResponse(mimetype=mimetype)
        if encoding:
            response["Content-Encoding"] = encoding
        try:
            response['X-Accel-Redirect'] = os.path.join(basepath[len(settings.SITE_ROOT):],
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
                           context_instance=RequestContext(request))
    r.status_code = 500
    return r


def server_error_404(request, template_name='404.html'):
    """
    A simple 500 handler so we get media
    """
    r = render_to_response(template_name,
                           context_instance=RequestContext(request))
    r.status_code = 404
    return r


def divide_by_zero(request):
    return 1 / 0


def morelikethis(request, project_slug, filename):
    project = get_object_or_404(Project, slug=project_slug)
    file = get_object_or_404(ImportedFile, project=project, path=filename)
    # sqs = SearchQuerySet().filter(project=project).more_like_this(file)[:5]
    sqs = SearchQuerySet().more_like_this(file)[:5]
    if len(sqs):
        output = [(obj.title, obj.absolute_url) for obj in sqs]
        json_response = json.dumps(output)
    else:
        json_response = {"message": "Not Found"}
    jsonp = "%s(%s)" % (request.GET.get('callback'), json_response)
    return HttpResponse(jsonp, mimetype='text/javascript')


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
        # causes solr request #1
        context['facets'] = self.results.facet_counts()
        context['form'] = self.form
        context['query'] = self.query
        context['selected_facets'] = ('&'.join(self.selected_facets)
                                      if self.selected_facets else '')
        context['selected_facets_list'] = self.selected_facets_list
        context['results'] = self.results
        context['count'] = len(self.results)  # causes solr request #2
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
