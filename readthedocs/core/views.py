"""Core views, including the main homepage, post-commit build hook,
documentation and header rendering, and server errors.

"""

from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve
from django.views.generic import TemplateView, FormView

from haystack.query import EmptySearchQuerySet
from haystack.query import SearchQuerySet

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.core.forms import FacetedSearchForm, SendEmailForm
from readthedocs.core.utils import trigger_build, broadcast, send_email
from readthedocs.donate.mixins import DonateProgressMixin
from readthedocs.builds.constants import LATEST
from readthedocs.projects import constants
from readthedocs.projects.models import Project, ImportedFile, ProjectRelationship
from readthedocs.projects.tasks import remove_dir, update_imported_docs
from readthedocs.redirects.utils import get_redirect_response

import json
import mimetypes
import os
import logging
import re

log = logging.getLogger(__name__)
pc_log = logging.getLogger(__name__ + '.post_commit')


class NoProjectException(Exception):
    pass


class HomepageView(DonateProgressMixin, TemplateView):

    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        '''Add latest builds and featured projects'''
        context = super(HomepageView, self).get_context_data(**kwargs)
        latest = []
        latest_builds = (
            Build.objects
            .filter(
                project__privacy_level=constants.PUBLIC,
                success=True,
            )
            .order_by('-date')
        )[:100]
        for build in latest_builds:
            if (build.project not in latest and len(latest) < 10):
                latest.append(build.project)
        context['project_list'] = latest
        context['featured_list'] = Project.objects.filter(featured=True)
        return context


class SupportView(TemplateView):
    template_name = 'support.html'

    def get_context_data(self, **kwargs):
        context = super(SupportView, self).get_context_data(**kwargs)
        support_email = getattr(settings, 'SUPPORT_EMAIL', None)
        if not support_email:
            support_email = 'support@{domain}'.format(
                domain=getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org'))

        context['support_email'] = support_email
        return context


def random_page(request, project_slug=None):
    imported_file = ImportedFile.objects.order_by('?')
    if project_slug:
        imported_file = imported_file.filter(project__slug=project_slug)
    imported_file = imported_file.first()
    if imported_file is None:
        raise Http404
    url = imported_file.get_absolute_url()
    return HttpResponseRedirect(url)


def live_builds(request):
    builds = Build.objects.filter(state='building')[:5]
    websocket_host = getattr(settings, 'WEBSOCKET_HOST', 'localhost:8088')
    count = builds.count()
    percent = 100
    if count > 1:
        percent = 100 / count
    return render_to_response('all_builds.html',
                              {'builds': builds,
                               'build_percent': percent,
                               'websocket_host': websocket_host},
                              context_instance=RequestContext(request))


@csrf_exempt
def wipe_version(request, project_slug, version_slug):
    version = get_object_or_404(Version, project__slug=project_slug,
                                slug=version_slug)
    if request.user not in version.project.users.all():
        raise Http404("You must own this project to wipe it.")

    if request.method == 'POST':
        del_dirs = [
            os.path.join(version.project.doc_path, 'checkouts', version.slug),
            os.path.join(version.project.doc_path, 'envs', version.slug),
            os.path.join(version.project.doc_path, 'conda', version.slug),
        ]
        for del_dir in del_dirs:
            broadcast(type='build', task=remove_dir, args=[del_dir])
        return redirect('project_version_list', project_slug)
    else:
        return render_to_response('wipe_version.html',
                                  context_instance=RequestContext(request))


def _build_version(project, slug, already_built=()):
    """
    Where we actually trigger builds for a project and slug.

    All webhook logic should route here to call ``trigger_build``.
    """
    default = project.default_branch or (project.vcs_repo().fallback_branch)
    if not project.has_valid_webhook:
        project.has_valid_webhook = True
        project.save()
    if slug == default and slug not in already_built:
        # short circuit versions that are default
        # these will build at "latest", and thus won't be
        # active
        latest_version = project.versions.get(slug=LATEST)
        trigger_build(project=project, version=latest_version, force=True)
        pc_log.info(("(Version build) Building %s:%s"
                     % (project.slug, latest_version.slug)))
        if project.versions.exclude(active=False).filter(slug=slug).exists():
            # Handle the case where we want to build the custom branch too
            slug_version = project.versions.get(slug=slug)
            trigger_build(project=project, version=slug_version, force=True)
            pc_log.info(("(Version build) Building %s:%s"
                         % (project.slug, slug_version.slug)))
        return LATEST
    elif project.versions.exclude(active=True).filter(slug=slug).exists():
        pc_log.info(("(Version build) Not Building %s" % slug))
        return None
    elif slug not in already_built:
        version = project.versions.get(slug=slug)
        trigger_build(project=project, version=version, force=True)
        pc_log.info(("(Version build) Building %s:%s"
                     % (project.slug, version.slug)))
        return slug
    else:
        pc_log.info(("(Version build) Not Building %s" % slug))
        return None


def _build_branches(project, branch_list):
    """
    Build the branches for a specific project.

    Returns:
        to_build - a list of branches that were built
        not_building - a list of branches that we won't build
    """
    for branch in branch_list:
        versions = project.versions_from_branch_name(branch)
        to_build = set()
        not_building = set()
        for version in versions:
            pc_log.info(("(Branch Build) Processing %s:%s"
                         % (project.slug, version.slug)))
            ret = _build_version(project, version.slug, already_built=to_build)
            if ret:
                to_build.add(ret)
            else:
                not_building.add(version.slug)
    return (to_build, not_building)


def get_project_from_url(url):
    projects = (
        Project.objects.filter(repo__iendswith=url) |
        Project.objects.filter(repo__iendswith=url + '.git'))
    return projects


def pc_log_info(project, msg):
    pc_log.info(constants.LOG_TEMPLATE
                .format(project=project,
                        version='',
                        msg=msg))


def _build_url(url, projects, branches):
    """
    Map a URL onto specific projects to build that are linked to that URL.

    Check each of the ``branches`` to see if they are active and should be built.
    """
    ret = ""
    all_built = {}
    all_not_building = {}
    for project in projects:
        (built, not_building) = _build_branches(project, branches)
        if not built:
            # Call update_imported_docs to update tag/branch info
            update_imported_docs.delay(project.versions.get(slug=LATEST).pk)
            msg = '(URL Build) Syncing versions for %s' % project.slug
            pc_log.info(msg)
        all_built[project.slug] = built
        all_not_building[project.slug] = not_building

    for project_slug, built in all_built.items():
        if built:
            msg = '(URL Build) Build Started: %s [%s]' % (
                url, ' '.join(built))
            pc_log_info(project_slug, msg=msg)
            ret += msg

    for project_slug, not_building in all_not_building.items():
        if not_building:
            msg = '(URL Build) Not Building: %s [%s]' % (
                url, ' '.join(not_building))
            pc_log_info(project_slug, msg=msg)
            ret += msg

    if not ret:
        ret = '(URL Build) No known branches were pushed to.'

    return HttpResponse(ret)


@csrf_exempt
def github_build(request):
    """
    A post-commit hook for github.
    """
    if request.method == 'POST':
        try:
            # GitHub RTD integration
            obj = json.loads(request.POST['payload'])
        except:
            # Generic post-commit hook
            obj = json.loads(request.body)
        repo_url = obj['repository']['url']
        hacked_repo_url = repo_url.replace('http://', '').replace('https://', '')
        ssh_url = obj['repository']['ssh_url']
        hacked_ssh_url = ssh_url.replace('git@', '').replace('.git', '')
        try:
            branch = obj['ref'].replace('refs/heads/', '')
        except KeyError:
            response = HttpResponse('ref argument required to build branches.')
            response.status_code = 400
            return response

        try:
            repo_projects = get_project_from_url(hacked_repo_url)
            if repo_projects:
                pc_log.info("(Incoming GitHub Build) %s [%s]" % (hacked_repo_url, branch))
            ssh_projects = get_project_from_url(hacked_ssh_url)
            if ssh_projects:
                pc_log.info("(Incoming GitHub Build) %s [%s]" % (hacked_ssh_url, branch))
            projects = repo_projects | ssh_projects
            return _build_url(hacked_repo_url, projects, [branch])
        except NoProjectException:
            pc_log.error(
                "(Incoming GitHub Build) Repo not found:  %s" % hacked_repo_url)
            return HttpResponseNotFound('Repo not found: %s' % hacked_repo_url)
    else:
        return HttpResponse("You must POST to this resource.")


@csrf_exempt
def gitlab_build(request):
    """
    A post-commit hook for GitLab.
    """
    if request.method == 'POST':
        try:
            # GitLab RTD integration
            obj = json.loads(request.POST['payload'])
        except:
            # Generic post-commit hook
            obj = json.loads(request.body)
        url = obj['repository']['homepage']
        ghetto_url = url.replace('http://', '').replace('https://', '')
        branch = obj['ref'].replace('refs/heads/', '')
        pc_log.info("(Incoming GitLab Build) %s [%s]" % (ghetto_url, branch))
        projects = get_project_from_url(ghetto_url)
        if projects:
            return _build_url(ghetto_url, projects, [branch])
        else:
            pc_log.error(
                "(Incoming GitLab Build) Repo not found:  %s" % ghetto_url)
            return HttpResponseNotFound('Repo not found: %s' % ghetto_url)
    else:
        return HttpResponse("You must POST to this resource.")


@csrf_exempt
def bitbucket_build(request):
    if request.method == 'POST':
        payload = request.POST.get('payload')
        pc_log.info("(Incoming Bitbucket Build) Raw: %s" % payload)
        if not payload:
            return HttpResponseNotFound('Invalid Request')
        obj = json.loads(payload)
        rep = obj['repository']
        branches = [rec.get('branch', '') for rec in obj['commits']]
        ghetto_url = "%s%s" % (
            "bitbucket.org", rep['absolute_url'].rstrip('/'))
        pc_log.info("(Incoming Bitbucket Build) %s [%s]" % (
            ghetto_url, ' '.join(branches)))
        pc_log.info("(Incoming Bitbucket Build) JSON: \n\n%s\n\n" % obj)
        projects = get_project_from_url(ghetto_url)
        if projects:
            return _build_url(ghetto_url, projects, branches)
        else:
            pc_log.error(
                "(Incoming Bitbucket Build) Repo not found:  %s" % ghetto_url)
            return HttpResponseNotFound('Repo not found: %s' % ghetto_url)
    else:
        return HttpResponse("You must POST to this resource.")


@csrf_exempt
def generic_build(request, project_id_or_slug=None):
    try:
        project = Project.objects.get(pk=project_id_or_slug)
    # Allow slugs too
    except (Project.DoesNotExist, ValueError):
        try:
            project = Project.objects.get(slug=project_id_or_slug)
        except (Project.DoesNotExist, ValueError):
            pc_log.error(
                "(Incoming Generic Build) Repo not found:  %s" % (
                    project_id_or_slug))
            return HttpResponseNotFound(
                'Repo not found: %s' % project_id_or_slug)
    if request.method == 'POST':
        slug = request.POST.get('version_slug', project.default_version)
        pc_log.info(
            "(Incoming Generic Build) %s [%s]" % (project.slug, slug))
        _build_version(project, slug)
    else:
        return HttpResponse("You must POST to this resource.")
    return redirect('builds_project_list', project.slug)


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
    if project_slug:
        try:
            proj = Project.objects.get(slug=project_slug)
        except (Project.DoesNotExist, ValueError):
            # Try with underscore, for legacy
            try:
                proj = Project.objects.get(slug=project_slug.replace('-', '_'))
            except (Project.DoesNotExist):
                proj = None
    else:
        # If project_slug isn't in URL pattern, it's set in subdomain
        # middleware as request.slug.
        try:
            proj = Project.objects.get(slug=request.slug)
        except (Project.DoesNotExist, ValueError):
            # Try with underscore, for legacy
            try:
                proj = Project.objects.get(slug=request.slug.replace('-', '_'))
            except (Project.DoesNotExist):
                proj = None
    if not proj:
        raise Http404("Project slug not found")
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
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_version_slug(request, version_slug, project_slug=None):
    """Redirect /latest/ to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['version_slug'] = version_slug
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_project_slug(request, project_slug=None):
    """Redirect / to /en/latest/."""
    kwargs = default_docs_kwargs(request, project_slug)
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def redirect_page_with_filename(request, filename, project_slug=None):
    """Redirect /page/file.html to /en/latest/file.html."""
    kwargs = default_docs_kwargs(request, project_slug)
    kwargs['filename'] = filename
    url = reverse('docs_detail', kwargs=kwargs)
    return HttpResponseRedirect(url)


def serve_docs(request, lang_slug, version_slug, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    try:
        proj = Project.objects.protected(request.user).get(slug=project_slug)
        ver = Version.objects.public(request.user).get(
            project__slug=project_slug, slug=version_slug)
    except (Project.DoesNotExist, Version.DoesNotExist):
        proj = None
        ver = None
    if not proj or not ver:
        return server_helpful_404(request, project_slug, lang_slug, version_slug,
                                  filename)

    if ver not in proj.versions.public(request.user, proj, only_active=False):
        r = render_to_response('401.html',
                               context_instance=RequestContext(request))
        r.status_code = 401
        return r
    return _serve_docs(request, project=proj, version=ver, filename=filename,
                       lang_slug=lang_slug, version_slug=version_slug,
                       project_slug=project_slug)


def _serve_docs(request, project, version, filename, lang_slug=None,
                version_slug=None, project_slug=None):
    '''Actually serve the built documentation files

    This is not called directly, but is wrapped by :py:func:`serve_docs` so that
    authentication can be manipulated.
    '''
    # Figure out actual file to serve
    if not filename:
        filename = "index.html"
    # This is required because we're forming the filenames outselves instead of
    # letting the web server do it.
    elif (
            (project.documentation_type == 'sphinx_htmldir' or
             project.documentation_type == 'mkdocs') and
            "_static" not in filename and
            ".css" not in filename and
            ".js" not in filename and
            ".png" not in filename and
            ".jpg" not in filename and
            ".svg" not in filename and
            "_images" not in filename and
            ".html" not in filename and
            "font" not in filename and
            "inv" not in filename):
        filename += "index.html"
    else:
        filename = filename.rstrip('/')
    # Use the old paths if we're on our old location.
    # Otherwise use the new language symlinks.
    # This can be removed once we have 'en' symlinks for every project.
    if lang_slug == project.language:
        basepath = project.rtd_build_path(version_slug)
    else:
        basepath = project.translations_symlink_path(lang_slug)
        basepath = os.path.join(basepath, version_slug)

    # Serve file
    log.info('Serving %s for %s' % (filename, project))
    if not settings.DEBUG and not getattr(settings, 'PYTHON_MEDIA', False):
        fullpath = os.path.join(basepath, filename)
        content_type, encoding = mimetypes.guess_type(fullpath)
        content_type = content_type or 'application/octet-stream'
        response = HttpResponse(content_type=content_type)
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


def serve_single_version_docs(request, filename, project_slug=None):
    if not project_slug:
        project_slug = request.slug
    proj = get_object_or_404(Project, slug=project_slug)

    # This function only handles single version projects
    if not proj.single_version:
        raise Http404

    return serve_docs(request, proj.language, proj.default_version,
                      filename, project_slug)


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
    A simple 404 handler so we get media
    """
    response = get_redirect_response(request, path=request.get_full_path())
    if response:
        return response
    r = render_to_response(template_name,
                           context_instance=RequestContext(request))
    r.status_code = 404
    return r


def server_helpful_404(
        request, project_slug=None, lang_slug=None, version_slug=None,
        filename=None, template_name='404.html'):
    response = get_redirect_response(request, path=filename)
    if response:
        return response
    pagename = re.sub(
        r'/index$', r'', re.sub(r'\.html$', r'', re.sub(r'/$', r'', filename)))
    suggestion = get_suggestion(
        project_slug, lang_slug, version_slug, pagename, request.user)
    r = render_to_response(template_name,
                           {'suggestion': suggestion},
                           context_instance=RequestContext(request))
    r.status_code = 404
    return r


def get_suggestion(project_slug, lang_slug, version_slug, pagename, user):
    """
    | # | project | version | language | What to show |
    | 1 |    0    |    0    |     0    | Error message |
    | 2 |    0    |    0    |     1    | Error message (Can't happen) |
    | 3 |    0    |    1    |     0    | Error message (Can't happen) |
    | 4 |    0    |    1    |     1    | Error message (Can't happen) |
    | 5 |    1    |    0    |     0    | A link to top-level page of default version |
    | 6 |    1    |    0    |     1    | Available versions on the translation project |
    | 7 |    1    |    1    |     0    | Available translations of requested version |
    | 8 |    1    |    1    |     1    | A link to top-level page of requested version |
    """

    suggestion = {}
    if project_slug:
        try:
            proj = Project.objects.get(slug=project_slug)
            if not lang_slug:
                lang_slug = proj.language
            try:
                ver = Version.objects.get(
                    project__slug=project_slug, slug=version_slug)
            except Version.DoesNotExist:
                ver = None

            if ver:  # if requested version is available on main project
                if lang_slug != proj.language:
                    try:
                        translations = proj.translations.filter(
                            language=lang_slug)
                        if translations:
                            ver = Version.objects.get(
                                project__slug=translations[0].slug, slug=version_slug)
                        else:
                            ver = None
                    except Version.DoesNotExist:
                        ver = None
                # if requested version is available on translation project too
                if ver:
                    # Case #8: Show a link to top-level page of the version
                    suggestion['type'] = 'top'
                    suggestion['message'] = "What are you looking for?"
                    suggestion['href'] = proj.get_docs_url(ver.slug, lang_slug)
                # requested version is available but not in requested language
                else:
                    # Case #7: Show available translations of the version
                    suggestion['type'] = 'list'
                    suggestion['message'] = (
                        "Requested page seems not to be translated in "
                        "requested language. But it's available in these "
                        "languages.")
                    suggestion['list'] = []
                    suggestion['list'].append({
                        'label': proj.language,
                        'project': proj,
                        'version_slug': version_slug,
                        'pagename': pagename
                    })
                    for t in proj.translations.all():
                        try:
                            Version.objects.get(
                                project__slug=t.slug, slug=version_slug)
                            suggestion['list'].append({
                                'label': t.language,
                                'project': t,
                                'version_slug': version_slug,
                                'pagename': pagename
                            })
                        except Version.DoesNotExist:
                            pass
            else:  # requested version does not exist on main project
                if lang_slug == proj.language:
                    trans = proj
                else:
                    translations = proj.translations.filter(language=lang_slug)
                    trans = translations[0] if translations else None
                if trans:  # requested language is available
                    # Case #6: Show available versions of the translation
                    suggestion['type'] = 'list'
                    suggestion['message'] = (
                        "Requested version seems not to have been built yet. "
                        "But these versions are available.")
                    suggestion['list'] = []
                    for v in Version.objects.public(user, trans, True):
                        suggestion['list'].append({
                            'label': v.slug,
                            'project': trans,
                            'version_slug': v.slug,
                            'pagename': pagename
                        })
                # requested project exists but requested version and language
                # are not available.
                else:
                    # Case #5: Show a link to top-level page of default version
                    # of main project
                    suggestion['type'] = 'top'
                    suggestion['message'] = 'What are you looking for??'
                    suggestion['href'] = proj.get_docs_url()
        except Project.DoesNotExist:
            # Case #1-4: Show error mssage
            suggestion['type'] = 'none'
            suggestion[
                'message'] = "We're sorry, we don't know what you're looking for"
    else:
        suggestion['type'] = 'none'
        suggestion[
            'message'] = "We're sorry, we don't know what you're looking for"

    return suggestion


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
    return HttpResponse(jsonp, content_type='text/javascript')


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


class SendEmailView(FormView):

    """Form view for sending emails to users from admin pages

    Accepts the following additional parameters:

    queryset
        The queryset to use to determine the users to send emails to
    """

    form_class = SendEmailForm
    template_name = 'core/send_email_form.html'

    def get_form_kwargs(self):
        """Override form kwargs based on input fields

        The admin posts to this view initially, so detect the send button on
        form post variables. Drop additional fields if we see the send button.
        """
        kwargs = super(SendEmailView, self).get_form_kwargs()
        if 'send' not in self.request.POST:
            kwargs.pop('data', None)
            kwargs.pop('files', None)
        return kwargs

    def get_initial(self):
        """Add selected ids to initial form data"""
        initial = super(SendEmailView, self).get_initial()
        initial['_selected_action'] = self.request.POST.getlist(
            admin.ACTION_CHECKBOX_NAME)
        return initial

    def form_valid(self, form):
        """If form is valid, send emails to selected users"""
        count = 0
        for user in self.get_queryset().all():
            send_email(
                user.email,
                subject=form.cleaned_data['subject'],
                template='core/email/common.txt',
                template_html='core/email/common.html',
                context={'user': user, 'content': form.cleaned_data['body']},
                request=self.request,
            )
            count += 1
        if count == 0:
            self.message_user("No receipients to send to", level=messages.ERROR)
        else:
            self.message_user("Queued {0} messages".format(count))
        return HttpResponseRedirect(self.request.get_full_path())

    def get_queryset(self):
        return self.kwargs.get('queryset')

    def get_context_data(self, **kwargs):
        """Return queryset in context"""
        context = super(SendEmailView, self).get_context_data(**kwargs)
        context['users'] = self.get_queryset().all()
        return context

    def message_user(self, message, level=messages.INFO, extra_tags='',
                     fail_silently=False):
        """Implementation of :py:meth:`django.contrib.admin.options.ModelAdmin.message_user`

        Send message through messages framework
        """
        # TODO generalize this or check if implementation in ModelAdmin is
        # useable here
        messages.add_message(self.request, level, message, extra_tags=extra_tags,
                             fail_silently=fail_silently)
