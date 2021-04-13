"""OAuth utility functions."""

import json
import logging
import re

from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter,
)
from django.conf import settings
from django.urls import reverse
from requests.exceptions import RequestException

from readthedocs.builds import utils as build_utils
from readthedocs.integrations.models import Integration

from ..models import RemoteOrganization, RemoteRepository
from .base import Service, SyncServiceError


log = logging.getLogger(__name__)


class BitbucketService(Service):

    """Provider service for Bitbucket."""

    adapter = BitbucketOAuth2Adapter
    # TODO replace this with a less naive check
    url_pattern = re.compile(r'bitbucket.org')
    https_url_pattern = re.compile(r'^https:\/\/[^@]+@bitbucket.org/')

    def sync_repositories(self):
        """Sync repositories from Bitbucket API."""
        remote_repositories = []

        # Get user repos
        try:
            repos = self.paginate(
                'https://bitbucket.org/api/2.0/repositories/?role=member',
            )
            for repo in repos:
                remote_repository = self.create_repository(repo)
                remote_repositories.append(remote_repository)

        except (TypeError, ValueError):
            log.warning('Error syncing Bitbucket repositories')
            raise SyncServiceError(
                'Could not sync your Bitbucket repositories, '
                'try reconnecting your account'
            )

        # Because privileges aren't returned with repository data, run query
        # again for repositories that user has admin role for, and update
        # existing repositories.
        try:
            resp = self.paginate(
                'https://bitbucket.org/api/2.0/repositories/?role=admin',
            )
            admin_repos = (
                RemoteRepository.objects.filter(
                    users=self.user,
                    full_name__in=[r['full_name'] for r in resp],
                    account=self.account,
                )
            )
            for repo in admin_repos:
                repo.admin = True
                repo.save()
        except (TypeError, ValueError):
            pass

        return remote_repositories

    def sync_organizations(self):
        """Sync Bitbucket teams (our RemoteOrganization) and team repositories."""
        remote_organizations = []
        remote_repositories = []

        try:
            teams = self.paginate(
                'https://api.bitbucket.org/2.0/teams/?role=member',
            )
            for team in teams:
                remote_organization = self.create_organization(team)
                repos = self.paginate(team['links']['repositories']['href'])

                remote_organizations.append(remote_organization)

                for repo in repos:
                    remote_repository = self.create_repository(
                        repo,
                        organization=remote_organization,
                    )
                    remote_repositories.append(remote_repository)

        except ValueError:
            log.warning('Error syncing Bitbucket organizations')
            raise SyncServiceError(
                'Could not sync your Bitbucket team repositories, '
                'try reconnecting your account',
            )

        return remote_organizations, remote_repositories

    def create_repository(self, fields, privacy=None, organization=None):
        """
        Update or create a repository from Bitbucket API response.

        .. note::
            The :py:data:`admin` property is not set during creation, as
            permissions are not part of the returned repository data from
            Bitbucket.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        if any([
                (privacy == 'private'),
                (fields['is_private'] is False and privacy == 'public'),
        ]):
            repo, _ = RemoteRepository.objects.get_or_create(
                full_name=fields['full_name'],
                account=self.account,
            )
            if repo.organization and repo.organization != organization:
                log.debug(
                    'Not importing %s because mismatched orgs',
                    fields['name'],
                )
                return None

            repo.organization = organization
            repo.users.add(self.user)
            repo.name = fields['name']
            repo.description = fields['description']
            repo.private = fields['is_private']

            # Default to HTTPS, use SSH for private repositories
            clone_urls = {
                u['name']: u['href']
                for u in fields['links']['clone']
            }
            repo.clone_url = self.https_url_pattern.sub(
                'https://bitbucket.org/',
                clone_urls.get('https'),
            )
            repo.ssh_url = clone_urls.get('ssh')
            if repo.private:
                repo.clone_url = repo.ssh_url

            repo.html_url = fields['links']['html']['href']
            repo.vcs = fields['scm']
            mainbranch = fields.get('mainbranch') or {}
            repo.default_branch = mainbranch.get('name')
            repo.account = self.account

            avatar_url = fields['links']['avatar']['href'] or ''
            repo.avatar_url = re.sub(r'\/16\/$', r'/32/', avatar_url)
            if not repo.avatar_url:
                repo.avatar_url = self.default_user_avatar_url

            repo.json = json.dumps(fields)
            repo.save()
            return repo

        log.debug(
            'Not importing %s because mismatched type',
            fields['name'],
        )

    def create_organization(self, fields):
        """
        Update or create remote organization from Bitbucket API response.

        :param fields: dictionary response of data from API
        :rtype: RemoteOrganization
        """
        organization, _ = RemoteOrganization.objects.get_or_create(
            slug=fields.get('username'),
            account=self.account,
        )
        organization.name = fields.get('display_name')
        organization.email = fields.get('email')
        organization.avatar_url = fields['links']['avatar']['href']
        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url
        organization.url = fields['links']['html']['href']
        organization.json = json.dumps(fields)
        organization.account = self.account
        organization.users.add(self.user)
        organization.save()
        return organization

    def get_next_url_to_paginate(self, response):
        return response.json().get('next')

    def get_paginated_results(self, response):
        return response.json().get('values', [])

    def get_webhook_data(self, project, integration):
        """Get webhook JSON data to post to the API."""
        return json.dumps({
            'description': 'Read the Docs ({domain})'.format(
                domain=settings.PRODUCTION_DOMAIN,
            ),
            'url': 'https://{domain}{path}'.format(
                domain=settings.PRODUCTION_DOMAIN,
                path=reverse(
                    'api_webhook',
                    kwargs={
                        'project_slug': project.slug,
                        'integration_pk': integration.pk,
                    },
                ),
            ),
            'active': True,
            'events': ['repo:push'],
        })

    def get_provider_data(self, project, integration):
        """
        Gets provider data from BitBucket Webhooks API.

        :param project: project
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: Dictionary containing provider data from the API or None
        :rtype: dict
        """

        if integration.provider_data:
            return integration.provider_data

        session = self.get_session()
        owner, repo = build_utils.get_bitbucket_username_repo(url=project.repo)

        rtd_webhook_url = 'https://{domain}{path}'.format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                'api_webhook',
                kwargs={
                    'project_slug': project.slug,
                    'integration_pk': integration.pk,
                },
            ),
        )

        try:
            resp = session.get(
                (
                    'https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/hooks'
                    .format(owner=owner, repo=repo)
                ),
            )

            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data["values"]:
                    if webhook_data["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            'Bitbucket integration updated with provider data for project: %s',
                            project,
                        )
                        break
            else:
                log.info(
                    'Bitbucket project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

        except Exception:
            log.exception(
                'Bitbucket webhook Listing failed for project: %s',
                project,
            )

        return integration.provider_data

    def setup_webhook(self, project, integration=None):
        """
        Set up Bitbucket project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: boolean based on webhook set up success, and requests Response object
        :rtype: (Bool, Response)
        """
        session = self.get_session()
        owner, repo = build_utils.get_bitbucket_username_repo(url=project.repo)

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.BITBUCKET_WEBHOOK,
            )
        data = self.get_webhook_data(project, integration)
        resp = None
        try:
            resp = session.post(
                (
                    'https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/hooks'
                    .format(owner=owner, repo=repo)
                ),
                data=data,
                headers={'content-type': 'application/json'},
            )
            if resp.status_code == 201:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info(
                    'Bitbucket webhook creation successful for project: %s',
                    project,
                )
                return (True, resp)

            if resp.status_code in [401, 403, 404]:
                log.info(
                    'Bitbucket project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception(
                'Bitbucket webhook creation failed for project: %s',
                project,
            )
        else:
            log.error(
                'Bitbucket webhook creation failed for project: %s',
                project,
            )
            try:
                log.debug(
                    'Bitbucket webhook creation failure response: %s',
                    resp.json(),
                )
            except ValueError:
                pass

        return (False, resp)

    def update_webhook(self, project, integration):
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Webhook integration to update
        :type integration: Integration
        :returns: boolean based on webhook set up success, and requests Response object
        :rtype: (Bool, Response)
        """
        provider_data = self.get_provider_data(project, integration)

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        session = self.get_session()
        data = self.get_webhook_data(project, integration)
        resp = None
        try:
            # Expect to throw KeyError here if provider_data is invalid
            url = provider_data['links']['self']['href']
            resp = session.put(
                url,
                data=data,
                headers={'content-type': 'application/json'},
            )

            if resp.status_code == 200:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info(
                    'Bitbucket webhook update successful for project: %s',
                    project,
                )
                return (True, resp)

            # Bitbucket returns 404 when the webhook doesn't exist. In this
            # case, we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

        # Catch exceptions with request or deserializing JSON
        except (KeyError, RequestException, TypeError, ValueError):
            log.exception(
                'Bitbucket webhook update failed for project: %s',
                project,
            )
        else:
            log.error(
                'Bitbucket webhook update failed for project: %s',
                project,
            )
            # Response data should always be JSON, still try to log if not though
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.debug(
                'Bitbucket webhook update failure response: %s',
                debug_data,
            )

        return (False, resp)
