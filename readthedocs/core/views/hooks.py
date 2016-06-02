import json

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
        (built, not_building) = _build_branches(project, branches)
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
    """A post-commit hook for github."""
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
                log.info("(Incoming GitHub Build) %s [%s]" % (hacked_repo_url, branch))
            ssh_projects = get_project_from_url(hacked_ssh_url)
            if ssh_projects:
                log.info("(Incoming GitHub Build) %s [%s]" % (hacked_ssh_url, branch))
            projects = repo_projects | ssh_projects
            return _build_url(hacked_repo_url, projects, [branch])
        except NoProjectException:
            log.error(
                "(Incoming GitHub Build) Repo not found:  %s" % hacked_repo_url)
            return HttpResponseNotFound('Repo not found: %s' % hacked_repo_url)
    else:
        return HttpResponse("You must POST to this resource.")


@csrf_exempt
def gitlab_build(request):
    """A post-commit hook for GitLab."""
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
        log.info("(Incoming GitLab Build) %s [%s]" % (ghetto_url, branch))
        projects = get_project_from_url(ghetto_url)
        if projects:
            return _build_url(ghetto_url, projects, [branch])
        else:
            log.error(
                "(Incoming GitLab Build) Repo not found:  %s" % ghetto_url)
            return HttpResponseNotFound('Repo not found: %s' % ghetto_url)
    else:
        return HttpResponse("You must POST to this resource.")


@csrf_exempt
def bitbucket_build(request):
    if request.method == 'POST':
        payload = request.POST.get('payload')
        log.info("(Incoming Bitbucket Build) Raw: %s" % payload)
        if not payload:
            return HttpResponseNotFound('Invalid Request')
        obj = json.loads(payload)
        rep = obj['repository']
        branches = [rec.get('branch', '') for rec in obj['commits']]
        ghetto_url = "%s%s" % (
            "bitbucket.org", rep['absolute_url'].rstrip('/'))
        log.info("(Incoming Bitbucket Build) %s [%s]" % (
            ghetto_url, ' '.join(branches)))
        log.info("(Incoming Bitbucket Build) JSON: \n\n%s\n\n" % obj)
        projects = get_project_from_url(ghetto_url)
        if projects:
            return _build_url(ghetto_url, projects, branches)
        else:
            log.error(
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
