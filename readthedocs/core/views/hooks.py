import json
import re

from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from readthedocs.core.utils import trigger_build
from readthedocs.builds.constants import LATEST
from readthedocs.projects import constants
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import update_imported_docs

import logging

log = logging.getLogger(__name__)


class NoProjectException(Exception):
    pass


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
        log.info(("(Version build) Building %s:%s"
                  % (project.slug, latest_version.slug)))
        if project.versions.exclude(active=False).filter(slug=slug).exists():
            # Handle the case where we want to build the custom branch too
            slug_version = project.versions.get(slug=slug)
            trigger_build(project=project, version=slug_version, force=True)
            log.info(("(Version build) Building %s:%s"
                      % (project.slug, slug_version.slug)))
        return LATEST
    elif project.versions.exclude(active=True).filter(slug=slug).exists():
        log.info(("(Version build) Not Building %s" % slug))
        return None
    elif slug not in already_built:
        version = project.versions.get(slug=slug)
        trigger_build(project=project, version=version, force=True)
        log.info(("(Version build) Building %s:%s"
                  % (project.slug, version.slug)))
        return slug
    else:
        log.info(("(Version build) Not Building %s" % slug))
        return None


def build_branches(project, branch_list):
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
            log.info(("(Branch Build) Processing %s:%s"
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


def log_info(project, msg):
    log.info(constants.LOG_TEMPLATE
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
        (built, not_building) = build_branches(project, branches)
        if not built:
            # Call update_imported_docs to update tag/branch info
            update_imported_docs.delay(project.versions.get(slug=LATEST).pk)
            msg = '(URL Build) Syncing versions for %s' % project.slug
            log.info(msg)
        all_built[project.slug] = built
        all_not_building[project.slug] = not_building

    for project_slug, built in all_built.items():
        if built:
            msg = '(URL Build) Build Started: %s [%s]' % (
                url, ' '.join(built))
            log_info(project_slug, msg=msg)
            ret += msg

    for project_slug, not_building in all_not_building.items():
        if not_building:
            msg = '(URL Build) Not Building: %s [%s]' % (
                url, ' '.join(not_building))
            log_info(project_slug, msg=msg)
            ret += msg

    if not ret:
        ret = '(URL Build) No known branches were pushed to.'

    return HttpResponse(ret)


@csrf_exempt
def github_build(request):
    """GitHub webhook consumer

    This will search for projects matching either a stripped down HTTP or SSH
    URL. The search is error prone, use the API v2 webhook for new webhooks.

    Old webhooks may not have specified the content type to POST with, and
    therefore can use ``application/x-www-form-urlencoded`` to pass the JSON
    payload. More information on the API docs here:
    https://developer.github.com/webhooks/creating/#content-type
    """
    if request.method == 'POST':
        try:
            if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
                data = json.loads(request.POST.get('payload'))
            else:
                data = json.loads(request.body)
            http_url = data['repository']['url']
            http_search_url = http_url.replace('http://', '').replace('https://', '')
            ssh_url = data['repository']['ssh_url']
            ssh_search_url = ssh_url.replace('git@', '').replace('.git', '')
            branches = [data['ref'].replace('refs/heads/', '')]
        except (ValueError, TypeError, KeyError):
            log.error('Invalid GitHub webhook payload', exc_info=True)
            return HttpResponse('Invalid request', status=400)
        try:
            repo_projects = get_project_from_url(http_search_url)
            if repo_projects:
                log.info(
                    'GitHub webhook search: url=%s branches=%s',
                    http_search_url,
                    branches
                )
            ssh_projects = get_project_from_url(ssh_search_url)
            if ssh_projects:
                log.info(
                    'GitHub webhook search: url=%s branches=%s',
                    ssh_search_url,
                    branches
                )
            projects = repo_projects | ssh_projects
            return _build_url(http_search_url, projects, branches)
        except NoProjectException:
            log.error('Project match not found: url=%s', http_search_url)
            return HttpResponseNotFound('Project not found')
    else:
        return HttpResponse('Method not allowed, POST is required', status=405)


@csrf_exempt
def gitlab_build(request):
    """GitLab webhook consumer

    Search project repository URLs using the site URL from GitLab webhook payload.
    This search is error-prone, use the API v2 webhook view for new webhooks.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data['project']['http_url']
            search_url = re.sub(r'^https?://(.*?)(?:\.git|)$', '\\1', url)
            branches = [data['ref'].replace('refs/heads/', '')]
        except (ValueError, TypeError, KeyError):
            log.error('Invalid GitLab webhook payload', exc_info=True)
            return HttpResponse('Invalid request', status=400)
        log.info(
            'GitLab webhook search: url=%s branches=%s',
            search_url,
            branches
        )
        projects = get_project_from_url(search_url)
        if projects:
            return _build_url(search_url, projects, branches)
        else:
            log.error('Project match not found: url=%s', search_url)
            return HttpResponseNotFound('Project match not found')
    else:
        return HttpResponse('Method not allowed, POST is required', status=405)


@csrf_exempt
def bitbucket_build(request):
    """Consume webhooks from multiple versions of Bitbucket's API

    New webhooks are set up with v2, but v1 webhooks will still point to this
    endpoint. There are also "services" that point here and submit
    ``application/x-www-form-urlencoded`` data.

    API v1
        https://confluence.atlassian.com/bitbucket/events-resources-296095220.html

    API v2
        https://confluence.atlassian.com/bitbucket/event-payloads-740262817.html#EventPayloads-Push

    Services
        https://confluence.atlassian.com/bitbucket/post-service-management-223216518.html
    """
    if request.method == 'POST':
        try:
            if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
                data = json.loads(request.POST.get('payload'))
            else:
                data = json.loads(request.body)

            version = 2 if request.META.get('HTTP_USER_AGENT') == 'Bitbucket-Webhooks/2.0' else 1
            if version == 1:
                branches = [commit.get('branch', '')
                            for commit in data['commits']]
                repository = data['repository']
                search_url = 'bitbucket.org{0}'.format(
                    repository['absolute_url'].rstrip('/')
                )
            elif version == 2:
                changes = data['push']['changes']
                branches = [change['new']['name']
                            for change in changes]
                search_url = 'bitbucket.org/{0}'.format(
                    data['repository']['full_name']
                )
        except (TypeError, ValueError, KeyError):
            log.error('Invalid Bitbucket webhook payload', exc_info=True)
            return HttpResponse('Invalid request', status=400)

        log.info(
            'Bitbucket webhook search: url=%s branches=%s',
            search_url,
            branches
        )
        log.debug('Bitbucket webhook payload:\n\n%s\n\n', data)
        projects = get_project_from_url(search_url)
        if projects:
            return _build_url(search_url, projects, branches)
        else:
            log.error('Project match not found: url=%s', search_url)
            return HttpResponseNotFound('Project match not found')
    else:
        return HttpResponse('Method not allowed, POST is required', status=405)


@csrf_exempt
def generic_build(request, project_id_or_slug=None):
    try:
        project = Project.objects.get(pk=project_id_or_slug)
    # Allow slugs too
    except (Project.DoesNotExist, ValueError):
        try:
            project = Project.objects.get(slug=project_id_or_slug)
        except (Project.DoesNotExist, ValueError):
            log.error(
                "(Incoming Generic Build) Repo not found:  %s" % (
                    project_id_or_slug))
            return HttpResponseNotFound(
                'Repo not found: %s' % project_id_or_slug)
    if request.method == 'POST':
        slug = request.POST.get('version_slug', project.default_version)
        log.info(
            "(Incoming Generic Build) %s [%s]" % (project.slug, slug))
        _build_version(project, slug)
    else:
        return HttpResponse("You must POST to this resource.")
    return redirect('builds_project_list', project.slug)
