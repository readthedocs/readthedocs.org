import logging

from allauth.socialaccount.models import SocialToken

from django.conf import settings
from requests_oauthlib import OAuth1Session, OAuth2Session

from .models import GithubProject, GithubOrganization, BitbucketProject
from readthedocs.restapi.client import api

log = logging.getLogger(__name__)


def get_oauth_session(user, provider):

    tokens = SocialToken.objects.filter(
        account__user__username=user.username, app__provider=provider)
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


def get_token_for_project(project, force_local=False):
    if not getattr(settings, 'ALLOW_PRIVATE_REPOS', False):
        return None
    token = None
    try:
        if getattr(settings, 'DONT_HIT_DB', True) and not force_local:
            token = api.project(project.pk).token().get()['token']
        else:
            for user in project.users.all():
                tokens = SocialToken.objects.filter(
                    account__user__username=user.username,
                    app__provider='github')
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

    session = get_oauth_session(user, provider='github')
    if sync and session:
        # Get user repos
        owner_resp = github_paginate(session, 'https://api.github.com/user/repos?per_page=100')
        try:
            for repo in owner_resp:
                GithubProject.objects.create_from_api(repo, user=user)
        except TypeError, e:
            print e

        # Get org repos
        try:
            resp = session.get('https://api.github.com/user/orgs')
            for org_json in resp.json():
                org_resp = session.get('https://api.github.com/orgs/%s' % org_json['login'])
                org_obj = GithubOrganization.objects.create_from_api(
                    org_resp.json(), user=user)
                # Add repos
                org_repos_resp = github_paginate(
                    session,
                    'https://api.github.com/orgs/%s/repos?per_page=100' % (
                        org_json['login']))
                for repo in org_repos_resp:
                    GithubProject.objects.create_from_api(
                        repo, user=user, organization=org_obj)
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


def process_bitbucket_json(user, json):
    try:
        for page in json:
            for repo in page['values']:
                BitbucketProject.objects.create_from_api(repo, user=user)
    except TypeError, e:
        print e


def import_bitbucket(user, sync):
    """ Do the actual github import """

    session = get_oauth_session(user, provider='bitbucket')
    if sync and session:
            # Get user repos
        try:
            owner_resp = bitbucket_paginate(
                session,
                'https://bitbucket.org/api/2.0/repositories/{owner}'.format(
                    owner=user.username))
            process_bitbucket_json(user, owner_resp)
        except TypeError, e:
            print e

        # Get org repos
        resp = session.get('https://bitbucket.org/api/1.0/user/privileges/')
        for team in resp.json()['teams'].keys():
            org_resp = bitbucket_paginate(
                session,
                'https://bitbucket.org/api/2.0/teams/{team}/repositories'.format(
                    team=team))
            process_bitbucket_json(user, org_resp)

    return session is not None
