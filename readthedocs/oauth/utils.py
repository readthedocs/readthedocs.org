import logging

from allauth.socialaccount.models import SocialToken

from django.conf import settings
from requests_oauthlib import OAuth2Session

from .models import GithubProject, GithubOrganization
from tastyapi import apiv2

log = logging.getLogger(__name__)


def make_github_project(user, org, privacy, repo_json):
    log.info('Trying GitHub: %s' % repo_json['full_name'])
    if (repo_json['private'] is True and privacy == 'private' or
            repo_json['private'] is False and privacy == 'public'):
        project, created = GithubProject.objects.get_or_create(
            full_name=repo_json['full_name'],
        )
        if project.organization and project.organization != org:
            log.debug('Not importing %s because mismatched orgs' % repo_json['name'])
            return None
        else:
            project.organization = org
        project.users.add(user)
        project.name = repo_json['name']
        project.description = repo_json['description']
        project.git_url = repo_json['git_url']
        project.ssh_url = repo_json['ssh_url']
        project.html_url = repo_json['html_url']
        project.json = repo_json
        project.save()
        return project
    else:
        log.debug('Not importing %s because mismatched type' % repo_json['name'])


def make_github_organization(user, org_json):
    org, created = GithubOrganization.objects.get_or_create(
        login=org_json.get('login'),
    )
    org.html_url = org_json.get('html_url')
    org.name = org_json.get('name')
    org.email = org_json.get('email')
    org.json = org_json
    org.users.add(user)
    org.save()
    return org


def get_token_for_project(project, force_local=False):
    if not getattr(settings, 'ALLOW_PRIVATE_REPOS', False):
        return None
    token = None
    try:
        if getattr(settings, 'DONT_HIT_DB', True) and not force_local:
            token = apiv2.project(project.pk).token().get()['token']
        else:
            for user in project.users.all():
                tokens = SocialToken.objects.filter(account__user__username=user.username, app__provider='github')
                if tokens.exists():
                    token = tokens[0].token
    except Exception:
        log.error('Failed to get token for user', exc_info=True)
    return token


def github_paginate(session, url):
    """
    Scans trough all github paginates results and returns the concatenated
    list of results.

    :param session: requests client instance
    :param url: start url to get the data from.

    See https://developer.github.com/v3/#pagination
    """
    result = []
    while url:
        r = session.get(url)
        result.extend(r.json())
        next = r.links.get('next')
        if next:
            url = next.get('url')
        else:
            url = None
    return result


def import_github(user, sync):
    """ Do the actual github import """

    repo_type = getattr(settings, 'GITHUB_PRIVACY', 'public')
    tokens = SocialToken.objects.filter(
        account__user__username=user.username, app__provider='github')
    github_connected = False
    if tokens.exists():
        github_connected = True
        if sync:
            token = tokens[0]
            session = OAuth2Session(
                client_id=token.app.client_id,
                token={
                    'access_token': str(token.token),
                    'token_type': 'bearer'
                }
            )
            # Get user repos
            owner_resp = github_paginate(session, 'https://api.github.com/user/repos?per_page=100')
            for repo in owner_resp:
                make_github_project(user=user, org=None, privacy=repo_type, repo_json=repo)

            # Get org repos
            resp = session.get('https://api.github.com/user/orgs')
            for org_json in resp.json():
                org_resp = session.get('https://api.github.com/orgs/%s' % org_json['login'])
                org_obj = make_github_organization(user=user, org_json=org_resp.json())
                # Add repos
                org_repos_resp = github_paginate(session, 'https://api.github.com/orgs/%s/repos?per_page=100' % org_json['login'])
                for repo in org_repos_resp:
                    make_github_project(user=user, org=org_obj, privacy=repo_type, repo_json=repo)

    return github_connected
