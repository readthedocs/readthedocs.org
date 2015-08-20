import logging
import json

from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from requests_oauthlib import OAuth1Session, OAuth2Session
from allauth.socialaccount.models import SocialToken, SocialAccount

from .models import GithubProject, GithubOrganization, BitbucketProject
from readthedocs.builds import utils as build_utils
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


def add_github_webhook(session, project):
    owner, repo = build_utils.get_github_username_repo(url=project.repo)
    data = json.dumps({
        'name': 'readthedocs',
        'active': True,
        'config': {'url': 'https://{domain}/github'.format(domain=settings.PRODUCTION_DOMAIN)}
    })
    resp = session.post(
        'https://api.github.com/repos/{owner}/{repo}/hooks'.format(owner=owner, repo=repo),
        data=data,
        headers={'content-type': 'application/json'}
    )
    log.info("Creating GitHub webhook response code: {code}".format(code=resp.status_code))
    return resp


def add_bitbucket_webhook(session, project):
    owner, repo = build_utils.get_bitbucket_username_repo(url=project.repo)
    data = {
        'type': 'POST',
        'url': 'https://{domain}/bitbucket'.format(domain=settings.PRODUCTION_DOMAIN),
    }
    resp = session.post(
        'https://api.bitbucket.org/1.0/repositories/{owner}/{repo}/services'.format(
            owner=owner, repo=repo
        ),
        data=data,
    )
    log.info("Creating BitBucket webhook response code: {code}".format(code=resp.status_code))
    return resp

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
    try:
        social_account = user.socialaccount_set.get(provider='bitbucket')
    except SocialAccount.DoesNotExist:
        log.exception('User tried to import from Bitbucket without a Social Account')
    if sync and session:
            # Get user repos
        try:
            owner_resp = bitbucket_paginate(
                session,
                'https://bitbucket.org/api/2.0/repositories/{owner}'.format(
                    owner=social_account.uid))
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
