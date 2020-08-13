"""OAuth utility functions."""

import json
import logging
import re

from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from requests.exceptions import RequestException

from readthedocs.api.v2.client import api
from readthedocs.builds import utils as build_utils
from readthedocs.builds.constants import (
    BUILD_STATUS_SUCCESS,
    SELECT_BUILD_STATUS,
)
from readthedocs.integrations.models import Integration

from ..models import RemoteOrganization, RemoteRepository
from .base import Service, SyncServiceError

log = logging.getLogger(__name__)


class GitHubService(Service):

    """Provider service for GitHub."""

    adapter = GitHubOAuth2Adapter
    # TODO replace this with a less naive check
    url_pattern = re.compile(r'github\.com')

    def sync(self):
        """Sync repositories and organizations."""
        repos = self.sync_repositories()
        organization_repos = self.sync_organizations()

        # Delete RemoteRepository where the user doesn't have access anymore
        # (skip RemoteRepository tied to a Project on this user)
        full_names = {repo.get('full_name') for repo in repos + organization_repos}
        self.user.oauth_repositories.exclude(
            Q(full_name__in=full_names) | Q(project__isnull=False)
        ).delete()

    def sync_repositories(self):
        """Sync repositories from GitHub API."""
        repos = self.paginate('https://api.github.com/user/repos?per_page=100')
        try:
            for repo in repos:
                self.create_repository(repo)
            return repos
        except (TypeError, ValueError):
            log.warning('Error syncing GitHub repositories')
            raise SyncServiceError(
                'Could not sync your GitHub repositories, '
                'try reconnecting your account'
            )

    def sync_organizations(self):
        """Sync organizations from GitHub API."""
        try:
            orgs = self.paginate('https://api.github.com/user/orgs')
            for org in orgs:
                org_resp = self.get_session().get(org['url'])
                org_obj = self.create_organization(org_resp.json())
                # Add repos
                # TODO ?per_page=100
                org_repos = self.paginate(
                    '{org_url}/repos'.format(org_url=org['url']),
                )
                for repo in org_repos:
                    self.create_repository(repo, organization=org_obj)
                return org_repos
        except (TypeError, ValueError):
            log.warning('Error syncing GitHub organizations')
            raise SyncServiceError(
                'Could not sync your GitHub organizations, '
                'try reconnecting your account'
            )

    def create_repository(self, fields, privacy=None, organization=None):
        """
        Update or create a repository from GitHub API response.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        if any([
                (privacy == 'private'),
                (fields['private'] is False and privacy == 'public'),
        ]):
            try:
                repo = RemoteRepository.objects.get(
                    full_name=fields['full_name'],
                    users=self.user,
                    account=self.account,
                )
            except RemoteRepository.DoesNotExist:
                repo = RemoteRepository.objects.create(
                    full_name=fields['full_name'],
                    account=self.account,
                )
                repo.users.add(self.user)
            if repo.organization and repo.organization != organization:
                log.debug(
                    'Not importing %s because mismatched orgs',
                    fields['name'],
                )
                return None

            repo.organization = organization
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
        Update or create remote organization from GitHub API response.

        :param fields: dictionary response of data from API
        :rtype: RemoteOrganization
        """
        try:
            organization = RemoteOrganization.objects.get(
                slug=fields.get('login'),
                users=self.user,
                account=self.account,
            )
        except RemoteOrganization.DoesNotExist:
            organization = RemoteOrganization.objects.create(
                slug=fields.get('login'),
                account=self.account,
            )
            organization.users.add(self.user)
        organization.url = fields.get('html_url')
        organization.name = fields.get('name')
        organization.email = fields.get('email')
        organization.avatar_url = fields.get('avatar_url')
        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url
        organization.json = json.dumps(fields)
        organization.account = self.account
        organization.save()
        return organization

    def get_next_url_to_paginate(self, response):
        return response.links.get('next', {}).get('url')

    def get_paginated_results(self, response):
        return response.json()

    def get_webhook_data(self, project, integration):
        """Get webhook JSON data to post to the API."""
        return json.dumps({
            'name': 'web',
            'active': True,
            'config': {
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
                'secret': integration.secret,
                'content_type': 'json',
            },
            'events': ['push', 'pull_request', 'create', 'delete'],
        })

    def get_provider_data(self, project, integration):
        """
        Gets provider data from GitHub Webhooks API.

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
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        rtd_webhook_url = 'https://{domain}{path}'.format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                'api_webhook',
                kwargs={
                    'project_slug': project.slug,
                    'integration_pk': integration.pk,
                },
            )
        )

        try:
            resp = session.get(
                (
                    'https://api.github.com/repos/{owner}/{repo}/hooks'
                    .format(owner=owner, repo=repo)
                ),
            )

            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data:
                    if webhook_data["config"]["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            'GitHub integration updated with provider data for project: %s',
                            project,
                        )
                        break
            else:
                log.info(
                    'GitHub project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

        except Exception:
            log.exception(
                'GitHub webhook Listing failed for project: %s',
                project,
            )

        return integration.provider_data

    def setup_webhook(self, project, integration=None):
        """
        Set up GitHub project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: boolean based on webhook set up success, and requests Response object
        :rtype: (Bool, Response)
        """
        session = self.get_session()
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.GITHUB_WEBHOOK,
            )

        if not integration.secret:
            integration.recreate_secret()

        data = self.get_webhook_data(project, integration)
        resp = None
        try:
            resp = session.post(
                (
                    'https://api.github.com/repos/{owner}/{repo}/hooks'
                    .format(owner=owner, repo=repo)
                ),
                data=data,
                headers={'content-type': 'application/json'},
            )

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info(
                    'GitHub webhook creation successful for project: %s',
                    project,
                )
                return (True, resp)

            if resp.status_code in [401, 403, 404]:
                log.info(
                    'GitHub project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

            # All other status codes will flow to the `else` clause below

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception(
                'GitHub webhook creation failed for project: %s',
                project,
            )
        else:
            log.error(
                'GitHub webhook creation failed for project: %s',
                project,
            )
            # Response data should always be JSON, still try to log if not
            # though
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.debug(
                'GitHub webhook creation failure response: %s',
                debug_data,
            )

        # Always remove the secret and return False if we don't return True above
        integration.remove_secret()
        return (False, resp)

    def update_webhook(self, project, integration):
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Webhook integration to update
        :type integration: Integration
        :returns: boolean based on webhook update success, and requests Response object
        :rtype: (Bool, Response)
        """
        session = self.get_session()
        if not integration.secret:
            integration.recreate_secret()
        data = self.get_webhook_data(project, integration)
        resp = None

        provider_data = self.get_provider_data(project, integration)

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        try:
            url = provider_data.get('url')

            resp = session.patch(
                url,
                data=data,
                headers={'content-type': 'application/json'},
            )

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info(
                    'GitHub webhook update successful for project: %s',
                    project,
                )
                return (True, resp)

            # GitHub returns 404 when the webhook doesn't exist. In this case,
            # we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

        # Catch exceptions with request or deserializing JSON
        except (AttributeError, RequestException, ValueError):
            log.exception(
                'GitHub webhook update failed for project: %s',
                project,
            )
        else:
            log.error(
                'GitHub webhook update failed for project: %s',
                project,
            )
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.debug(
                'GitHub webhook update failure response: %s',
                debug_data,
            )

        integration.remove_secret()
        return (False, resp)

    def send_build_status(self, build, commit, state):
        """
        Create GitHub commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param state: build state failure, pending, or success.
        :type state: str
        :param commit: commit sha of the pull request
        :type commit: str
        :returns: boolean based on commit status creation was successful or not.
        :rtype: Bool
        """
        session = self.get_session()
        project = build.project
        owner, repo = build_utils.get_github_username_repo(url=project.repo)

        # select the correct state and description.
        github_build_state = SELECT_BUILD_STATUS[state]['github']
        description = SELECT_BUILD_STATUS[state]['description']

        target_url = build.get_full_url()

        if state == BUILD_STATUS_SUCCESS:
            target_url = build.version.get_absolute_url()

        context = f'{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}'

        data = {
            'state': github_build_state,
            'target_url': target_url,
            'description': description,
            'context': context,
        }

        resp = None

        try:
            statuses_url = f'https://api.github.com/repos/{owner}/{repo}/statuses/{commit}'
            resp = session.post(
                statuses_url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
            )
            if resp.status_code == 201:
                log.info(
                    "GitHub commit status created for project: %s, commit status: %s",
                    project.slug,
                    github_build_state,
                )
                return True

            if resp.status_code in [401, 403, 404]:
                log.info(
                    'GitHub project does not exist or user does not have '
                    'permissions: project=%s, user=%s, status=%s, url=%s',
                    project.slug,
                    self.user.username,
                    resp.status_code,
                    statuses_url,
                )
                return False

            log.warning(
                'Unknown GitHub status API response: project=%s, user=%s, status_code=%s',
                project.slug,
                self.user,
                resp.status_code
            )
            return False

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception(
                'GitHub commit status creation failed for project: %s',
                project.slug,
            )
            # Response data should always be JSON, still try to log if not
            # though
            if resp is not None:
                try:
                    debug_data = resp.json()
                except ValueError:
                    debug_data = resp.content
            else:
                debug_data = resp

            log.debug(
                'GitHub commit status creation failure response: %s',
                debug_data,
            )
            return False

    @classmethod
    def get_token_for_project(cls, project, force_local=False):
        """Get access token for project by iterating over project users."""
        # TODO why does this only target GitHub?
        if not settings.ALLOW_PRIVATE_REPOS:
            return None
        token = None
        try:
            if settings.DONT_HIT_DB and not force_local:
                token = api.project(project.pk).token().get()['token']
            else:
                for user in project.users.all():
                    tokens = SocialToken.objects.filter(
                        account__user=user,
                        app__provider=cls.adapter.provider_id,
                    )
                    if tokens.exists():
                        token = tokens[0].token
        except Exception:
            log.exception('Failed to get token for project')
        return token
