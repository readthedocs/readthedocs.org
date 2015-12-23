"""OAuth utility functions"""

import logging
import json
import re
from datetime import datetime

from django.conf import settings

from requests_oauthlib import OAuth2Session
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

from readthedocs.builds import utils as build_utils
from readthedocs.restapi.client import api

from .models import RemoteOrganization, RemoteRepository


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')

log = logging.getLogger(__name__)


class Service(object):

    """Service mapping for local accounts

    :param user: User to use in token lookup and session creation
    :param account: :py:cls:`SocialAccount` instance for user
    """

    adapter = None

    def __init__(self, user, account):
        self.session = None
        self.user = user
        self.account = account

    @classmethod
    def for_user(cls, user):
        """Create instance if user has an account for the provider"""
        try:
            account = SocialAccount.objects.get(
                user=user,
                provider=cls.adapter.provider_id
            )
            return cls(user=user, account=account)
        except SocialAccount.DoesNotExist:
            return None

    def get_adapter(self):
        return self.adapter

    @property
    def provider_id(self):
        return self.get_adapter().provider_id

    def get_session(self):
        if self.session is None:
            self.create_session()
        return self.session

    def create_session(self):
        """Create OAuth session for user

        This configures the OAuth session based on the :py:cls:`SocialToken`
        attributes. If there is an ``expires_at``, treat the session as an auto
        renewing token. Some providers expire tokens after as little as 2
        hours.
        """
        token = self.account.socialtoken_set.first()
        if token is None:
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

        self.session = OAuth2Session(
            client_id=token.app.client_id,
            token=token_config,
            auto_refresh_kwargs={
                'client_id': token.app.client_id,
                'client_secret': token.app.secret,
            },
            auto_refresh_url=self.get_adapter().access_token_url,
            token_updater=self.token_updater(token)
        )

        return self.session or None

    def token_updater(self, token):
        """Update token given data from OAuth response

        Expect the following response into the closure::

            {
                u'token_type': u'bearer',
                u'scopes': u'webhook repository team account',
                u'refresh_token': u'...',
                u'access_token': u'...',
                u'expires_in': 3600,
                u'expires_at': 1449218652.558185
            }
        """

        def _updater(data):
            token.token = data['access_token']
            token.expires_at = datetime.fromtimestamp(data['expires_at'])
            token.save()
            log.info('Updated token %s:', token)

        return _updater

    def sync(self, sync):
        raise NotImplementedError

    def create_repository(self, fields, privacy=DEFAULT_PRIVACY_LEVEL,
                          organization=None):
        raise NotImplementedError

    def create_organization(self, fields):
        raise NotImplementedError

    def setup_webhook(self, project):
        raise NotImplementedError


class GitHubService(Service):

    """Provider service for GitHub"""

    adapter = GitHubOAuth2Adapter

    def sync(self, sync):
        """Sync repositories and organizations"""
        if sync:
            self.sync_repositories()
            self.sync_organizations()

    def sync_repositories(self):
        """Get repositories for GitHub user via OAuth token"""
        repos = self.paginate('https://api.github.com/user/repos?per_page=100')
        try:
            for repo in repos:
                self.create_repository(repo)
        except (TypeError, ValueError) as e:
            log.error('Error syncing GitHub repositories: %s',
                      str(e), exc_info=True)
            raise Exception('Could not sync your GitHub repositories, '
                            'try reconnecting your account')

    def sync_organizations(self):
        """Sync GitHub organizations and organization repositories"""
        try:
            orgs = self.paginate('https://api.github.com/user/orgs')
            for org in orgs:
                org_resp = self.get_session().get(org['url'])
                org_obj = self.create_organization(org_resp.json())
                # Add repos
                # TODO ?per_page=100
                org_repos = self.paginate(
                    '{org_url}/repos'.format(org_url=org['url'])
                )
                for repo in org_repos:
                    self.create_repository(repo, organization=org_obj)
        except (TypeError, ValueError) as e:
            log.error('Error syncing GitHub organizations: %s',
                      str(e), exc_info=True)
            raise Exception('Could not sync your GitHub organizations, '
                            'try reconnecting your account')

    def create_repository(self, fields, privacy=DEFAULT_PRIVACY_LEVEL,
                          organization=None):
        if (
                (privacy == 'private') or
                (fields['private'] is False and privacy == 'public')):
            repo, _ = RemoteRepository.objects.get_or_create(
                full_name=fields['full_name'],
                account=self.account,
            )
            if repo.organization and repo.organization != organization:
                log.debug('Not importing %s because mismatched orgs' %
                          fields['name'])
                return None
            else:
                repo.organization = organization
            repo.users.add(self.user)
            repo.name = fields['name']
            repo.description = fields['description']
            repo.ssh_url = fields['ssh_url']
            repo.html_url = fields['html_url']
            repo.private = fields['private']
            if repo.private:
                repo.clone_url = fields['ssh_url']
            else:
                repo.clone_url = fields['clone_url']
            repo.admin = fields.get('permissions', {}).get('admin', False)
            repo.vcs = 'git'
            repo.account = self.account
            repo.avatar_url = fields.get('owner', {}).get('avatar_url')
            repo.json = json.dumps(fields)
            repo.save()
            return repo
        else:
            log.debug('Not importing %s because mismatched type' %
                      fields['name'])

    def create_organization(self, fields):
        organization, _ = RemoteOrganization.objects.get_or_create(
            slug=fields.get('login'),
            account=self.account,
        )
        organization.html_url = fields.get('html_url')
        organization.name = fields.get('name')
        organization.email = fields.get('email')
        organization.avatar_url = fields.get('avatar_url')
        organization.json = json.dumps(fields)
        organization.account = self.account
        organization.users.add(self.user)
        organization.save()
        return organization

    def paginate(self, url):
        """Combines return from GitHub pagination

        :param url: start url to get the data from.

        See https://developer.github.com/v3/#pagination
        """
        resp = self.get_session().get(url)
        result = resp.json()
        next_url = resp.links.get('next', {}).get('url')
        if next_url:
            result.extend(self.paginate(next_url))
        return result

    def setup_webhook(self, project):
        """Set up GitHub webhook for project

        :param project: Project instance to set up webhook for
        """
        session = self.get_session()
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
        log.info("Creating GitHub webhook: response={code}"
                 .format(code=resp.status_code))
        return resp

    @classmethod
    def get_token_for_project(cls, project, force_local=False):
        """Get access token for project by iterating over project users"""
        # TODO why does this only target GitHub?
        if not getattr(settings, 'ALLOW_PRIVATE_REPOS', False):
            return None
        token = None
        try:
            if getattr(settings, 'DONT_HIT_DB', True) and not force_local:
                token = api.project(project.pk).token().get()['token']
            else:
                for user in project.users.all():
                    tokens = SocialToken.objects.filter(
                        account__user=user,
                        app__provider=cls.adapter.provider_id)
                    if tokens.exists():
                        token = tokens[0].token
        except Exception:
            log.error('Failed to get token for user', exc_info=True)
        return token


class BitbucketService(Service):

    """Provider service for Bitbucket"""

    adapter = BitbucketOAuth2Adapter

    def sync(self, sync):
        """Import from Bitbucket"""
        if sync:
            self.sync_repositories()
            self.sync_teams()

    def sync_repositories(self):
        # Get user repos
        try:
            repos = self.paginate(
                'https://bitbucket.org/api/2.0/repositories/?role=member')
            for repo in repos:
                self.create_repository(repo)
        except (TypeError, ValueError) as e:
            log.error('Error syncing Bitbucket repositories: %s',
                      str(e), exc_info=True)
            raise Exception('Could not sync your Bitbucket repositories, '
                            'try reconnecting your account')

        # Because privileges aren't returned with repository data, run query
        # again for repositories that user has admin role for, and update
        # existing repositories.
        try:
            resp = self.paginate(
                'https://bitbucket.org/api/2.0/repositories/?role=admin')
            repos = (
                RemoteRepository.objects
                .filter(users=self.user,
                        full_name__in=[r['full_name'] for r in resp],
                        account=self.account)
            )
            for repo in repos:
                repo.admin = True
                repo.save()
        except (TypeError, ValueError):
            pass

    def sync_teams(self):
        """Sync Bitbucket teams and team repositories for user token"""
        try:
            teams = self.paginate(
                'https://api.bitbucket.org/2.0/teams/?role=member'
            )
            for team in teams:
                org = self.create_organization(team)
                repos = self.paginate(team['links']['repositories']['href'])
                for repo in repos:
                    self.create_repository(repo, organization=org)
        except ValueError as e:
            log.error('Error syncing Bitbucket organizations: %s',
                      str(e), exc_info=True)
            raise Exception('Could not sync your Bitbucket team repositories, '
                            'try reconnecting your account')

    def create_repository(self, fields, privacy=DEFAULT_PRIVACY_LEVEL,
                          organization=None):
        """Update or create a repository from Bitbucket

        This looks up existing repositories based on the full repository name,
        that is the username and repository name.

        .. note::
            The :py:data:`admin` property is not set during creation, as
            permissions are not part of the returned repository data from
            Bitbucket.
        """
        if (fields['is_private'] is True and privacy == 'private' or
                fields['is_private'] is False and privacy == 'public'):
            repo, _ = RemoteRepository.objects.get_or_create(
                full_name=fields['full_name'],
                account=self.account,
            )
            if repo.organization and repo.organization != organization:
                log.debug('Not importing %s because mismatched orgs' %
                          fields['name'])
                return None
            else:
                repo.organization = organization
            repo.users.add(self.user)
            repo.name = fields['name']
            repo.description = fields['description']
            repo.private = fields['is_private']
            repo.clone_url = fields['links']['clone'][0]['href']
            repo.ssh_url = fields['links']['clone'][1]['href']
            if repo.private:
                repo.clone_url = repo.ssh_url
            repo.html_url = fields['links']['html']['href']
            repo.vcs = fields['scm']
            repo.account = self.account

            avatar_url = fields['links']['avatar']['href'] or ''
            repo.avatar_url = re.sub(r'\/16\/$', r'/32/', avatar_url)

            repo.json = json.dumps(fields)
            repo.save()
            return repo
        else:
            log.debug('Not importing %s because mismatched type' %
                      fields['name'])

    def create_organization(self, fields):
        organization, _ = RemoteOrganization.objects.get_or_create(
            slug=fields.get('username'),
            account=self.account,
        )
        organization.name = fields.get('display_name')
        organization.email = fields.get('email')
        organization.avatar_url = fields['links']['avatar']['href']
        organization.html_url = fields['links']['html']['href']
        organization.json = json.dumps(fields)
        organization.account = self.account
        organization.users.add(self.user)
        organization.save()
        return organization

    def paginate(self, url):
        """Combines results from Bitbucket pagination

        :param url: start url to get the data from.
        """
        resp = self.get_session().get(url)
        data = resp.json()
        results = data.get('values', [])
        next_url = data.get('next')
        if next_url:
            results.extend(self.paginate(next_url))
        return results

    def setup_webhook(self, project):
        session = self.get_session()
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


services = [GitHubService, BitbucketService]
