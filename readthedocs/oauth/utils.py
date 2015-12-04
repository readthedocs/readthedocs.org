"""OAuth utility functions"""

import logging
import json
from datetime import datetime

from django.conf import settings

from requests_oauthlib import OAuth1Session, OAuth2Session
from allauth.socialaccount.models import SocialToken, SocialAccount
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

from readthedocs.builds import utils as build_utils
from readthedocs.restapi.client import api

from .models import RemoteOrganization, RemoteRepository
from .constants import OAUTH_SOURCE_BITBUCKET


log = logging.getLogger(__name__)


def get_oauth_session(user, adapter):
    """Get OAuth session based on adapter"""
    tokens = SocialToken.objects.filter(
        account__user__username=user.username,
        app__provider=adapter.provider_id)
    if tokens.exists():
        token = tokens[0]
    else:
        return None
    token_config = {
        'access_token': str(token.token),
        'token_type': 'bearer',
    }
    if token.expires_at is not None:
        token_expires = (token.expires_at - datetime.now()).total_seconds()
        token_config.update({
            'refresh_token': str(token.token_secret),
            'expires_in': token_expires,
        })

    def save_token(data):
        """
        {
            u'token_type': u'bearer',
            u'scopes': u'webhook repository team account',
            u'refresh_token': u'...',
            u'access_token': u'...',
            u'expires_in': 3600,
            u'expires_at': 1449218652.558185
        }
        """
        token.token = data['access_token']
        token.expires_at = datetime.fromtimestamp(data['expires_at'])
        token.save()
        log.info('Updated token %s:', token)

    session = OAuth2Session(
        client_id=token.app.client_id,
        token=token_config,
        auto_refresh_kwargs={
            'client_id': token.app.client_id,
            'client_secret': token.app.secret,
        },
        auto_refresh_url=adapter.access_token_url,
        token_updater=save_token
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
                    app__provider=GitHubProvider.id)
                if tokens.exists():
                    token = tokens[0].token
    except Exception:
        log.error('Failed to get token for user', exc_info=True)
    return token


def github_paginate(session, url):
    """Combines return from GitHub pagination

    :param session: requests client instance
    :param url: start url to get the data from.

    See https://developer.github.com/v3/#pagination
    """
    result = []
    while url:
        r = session.get(url)
        result.extend(r.json())
        next_url = r.links.get('next')
        if next_url:
            url = next_url.get('url')
        else:
            url = None
    return result


def import_github(user, sync):
    """Do the actual github import"""
    session = get_oauth_session(user, adapter=GitHubOAuth2Adapter)
    if sync and session:
        # Get user repos
        owner_resp = github_paginate(session, 'https://api.github.com/user/repos?per_page=100')
        try:
            for repo in owner_resp:
                RemoteRepository.objects.create_from_github_api(repo, user=user)
        except (TypeError, ValueError):
            raise Exception('Could not sync your GitHub repositories, '
                            'try reconnecting your account')

        # Get org repos
        try:
            resp = session.get('https://api.github.com/user/orgs')
            for org_json in resp.json():
                org_resp = session.get('https://api.github.com/orgs/%s' % org_json['login'])
                org_obj = RemoteOrganization.objects.create_from_github_api(
                    org_resp.json(), user=user)
                # Add repos
                org_repos_resp = github_paginate(
                    session,
                    'https://api.github.com/orgs/%s/repos?per_page=100' % (
                        org_json['login']))
                for repo in org_repos_resp:
                    RemoteRepository.objects.create_from_github_api(
                        repo, user=user, organization=org_obj)
        except (TypeError, ValueError):
            raise Exception('Could not sync your GitHub organizations, '
                            'try reconnecting your account')

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
    """Combines results from Bitbucket pagination

    :param session: requests client instance
    :param url: start url to get the data from.

    """
    result = []
    while url:
        r = session.get(url)
        data = r.json()
        url = None
        result.extend(data.get('values', []))
        next_url = data.get('next')
        if next_url:
            url = next_url
    return result


def process_bitbucket_json(user, json):
    try:
        for page in json:
            for repo in page['values']:
                RemoteRepository.objects.create_from_bitbucket_api(repo,
                                                                   user=user)
    except TypeError, e:
        print e


def import_bitbucket(user, sync):
    """Import from Bitbucket"""
    session = get_oauth_session(user, adapter=BitbucketOAuth2Adapter)
    try:
        social_account = user.socialaccount_set.get(
            provider=BitbucketOAuth2Adapter.provider_id)
    except SocialAccount.DoesNotExist:
        pass
    if sync and session:
        # Get user repos
        try:
            repos = bitbucket_paginate(
                session,
                'https://bitbucket.org/api/2.0/repositories/?role=member')
            for repo in repos:
                RemoteRepository.objects.create_from_bitbucket_api(
                    repo,
                    user=user,
                )
        except (TypeError, ValueError):
            raise Exception('Could not sync your Bitbucket repositories, '
                            'try reconnecting your account')

        # Because privileges aren't returned with repository data, run query
        # again for repositories that user has admin role for, and update
        # existing repositories.
        try:
            resp = bitbucket_paginate(
                session,
                'https://bitbucket.org/api/2.0/repositories/?role=admin')
            repos = (
                RemoteRepository.objects
                .filter(users=user,
                        full_name__in=[r['full_name'] for r in resp],
                        source=OAUTH_SOURCE_BITBUCKET)
            )
            for repo in repos:
                repo.admin = True
                repo.save()
        except (TypeError, ValueError):
            pass

        # Get team repos
        try:
            teams = bitbucket_paginate(
                session,
                'https://api.bitbucket.org/2.0/teams/?role=member')
            for team_data in teams:
                org = RemoteOrganization.objects.create_from_bitbucket_api(
                    team_data, user=user)
                repos = bitbucket_paginate(
                    session,
                    team_data['links']['repositories']['href'])
                for repo in repos:
                    RemoteRepository.objects.create_from_bitbucket_api(
                        repo,
                        user=user,
                        organization=org,
                    )
        except ValueError:
            raise Exception('Could not sync your Bitbucket team repositories, '
                            'try reconnecting your account')

    return session is not None
