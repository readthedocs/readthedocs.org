"""OAuth utility functions"""

import logging
import json
import re

from django.conf import settings
from requests.exceptions import RequestException
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter)

from readthedocs.builds import utils as build_utils

from ..models import RemoteOrganization, RemoteRepository
from .base import Service


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')

log = logging.getLogger(__name__)


class BitbucketService(Service):

    """Provider service for Bitbucket"""

    adapter = BitbucketOAuth2Adapter
    # TODO replace this with a less naive check
    url_pattern = re.compile(r'bitbucket.org\/')

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
        organization.url = fields['links']['html']['href']
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
        data = json.dumps({
            'description': 'Read the Docs ({domain})'.format(domain=settings.PRODUCTION_DOMAIN),
            'url': 'https://{domain}/bitbucket'.format(domain=settings.PRODUCTION_DOMAIN),
            'active': True,
            'events': ['repo:push'],
        })
        try:
            resp = session.post(
                ('https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/hooks'
                 .format(owner=owner, repo=repo)),
                data=data,
                headers={'content-type': 'application/json'}
            )
            if resp.status_code == 201:
                log.info('Bitbucket webhook creation successful for project: %s',
                         project)
                return True
        except RequestException:
            log.error('Bitbucket webhook creation failed for project: %s',
                      project, exc_info=True)
        else:
            log.error('Bitbucket webhook creation failed for project: %s',
                      project)
            return False
