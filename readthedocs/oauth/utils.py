import logging

from allauth.socialaccount.models import SocialToken

from django.conf import settings
from requests_oauthlib import OAuth1Session, OAuth2Session

from .models import GithubProject, GithubOrganization, BitbucketProject, BitbucketTeam
from tastyapi import apiv2

log = logging.getLogger(__name__)


def get_oauth_session(user, provider):

    tokens = SocialToken.objects.filter(account__user__username=user.username, app__provider=provider)
    if tokens.exists():
        token = tokens[0]
    else:
        return None
    if provider == 'github':
        session = OAuth2Session(
            client_id=token.app.client_id,
            token={
                'access_token': str(token.token),
                'token_type': 'bearer'
            }
        )
    elif provider == 'bitbucket':
        session = OAuth1Session(
            token.app.client_id,
            client_secret=token.app.secret,
            resource_owner_key=token.token,
            resource_owner_secret=token.token_secret
        )

    return session or None


def make_github_project(user, org, privacy, repo_json):
    log.info('Trying GitHub: %s' % repo_json['full_name'])
    if (repo_json['private'] is True and privacy == 'private' or
            repo_json['private'] is False and privacy == 'public'):
        project, created = GithubProject.objects.get_or_create(
            full_name=repo_json['full_name'],
            users__pk=user.pk,
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
    session = get_oauth_session(user, provider='github')
    if sync and session:
        # Get user repos
        owner_resp = github_paginate(session, 'https://api.github.com/user/repos?per_page=100')
        try:
            for repo in owner_resp:
                make_github_project(user=user, org=None, privacy=repo_type, repo_json=repo)
        except TypeError, e:
            print e

        # Get org repos
        try:
            resp = session.get('https://api.github.com/user/orgs')
            for org_json in resp.json():
                org_resp = session.get('https://api.github.com/orgs/%s' % org_json['login'])
                org_obj = make_github_organization(user=user, org_json=org_resp.json())
                # Add repos
                org_repos_resp = github_paginate(session, 'https://api.github.com/orgs/%s/repos?per_page=100' % org_json['login'])
                for repo in org_repos_resp:
                    make_github_project(user=user, org=org_obj, privacy=repo_type, repo_json=repo)
        except TypeError, e:
            print e

    return session is not None


###
# Bitbucket
###


def bitbucket_paginate(session, url):
    """
    Scans trough all github paginates results and returns the concatenated
    list of results.

    :param session: requests client instance
    :param url: start url to get the data from.

    """
    result = []
    while url:
        r = session.get(url)
        result.extend([r.json()])
        next_url = r.json().get('next')
        if next_url:
            url = next_url
        else:
            url = None
    return result


def make_bitbucket_project(user, org, privacy, repo_json):
    log.info('Trying Bitbucket: %s' % repo_json['full_name'])
    if (repo_json['is_private'] is True and privacy == 'private' or
            repo_json['is_private'] is False and privacy == 'public'):
        project, created = BitbucketProject.objects.get_or_create(
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
        project.git_url = repo_json['links']['clone'][0]['href']
        project.ssh_url = repo_json['links']['clone'][1]['href']
        project.html_url = repo_json['links']['html']['href']
        project.vcs = repo_json['scm']
        project.json = repo_json
        project.save()
        return project
    else:
        log.debug('Not importing %s because mismatched type' % repo_json['name'])


def process_bitbucket_json(user, json, repo_type):
    try:
        for page in json:
            for repo in page['values']:
                make_bitbucket_project(user=user, org=None, privacy=repo_type, repo_json=repo)
    except TypeError, e:
        print e


def import_bitbucket(user, sync):
    """ Do the actual github import """

    repo_type = getattr(settings, 'GITHUB_PRIVACY', 'public')
    session = get_oauth_session(user, provider='bitbucket')
    if sync and session:
            # Get user repos
        try:
            owner_resp = bitbucket_paginate(session, 'https://bitbucket.org/api/2.0/repositories/{owner}'.format(owner=user.username))
            process_bitbucket_json(user, owner_resp, repo_type)
        except TypeError, e:
            print e

        # Get org repos
        resp = session.get('https://bitbucket.org/api/1.0/user/privileges/')
        for team in resp.json()['teams'].keys():
            org_resp = bitbucket_paginate(session, 'https://bitbucket.org/api/2.0/teams/{team}/repositories'.format(team=team))
            process_bitbucket_json(user, org_resp, repo_type)

    return session is not None
