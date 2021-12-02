"""OAuth utility functions."""

import json
import structlog
import re

from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from django.conf import settings
from django.urls import reverse
from requests.exceptions import RequestException

from readthedocs.api.v2.client import api
from readthedocs.builds import utils as build_utils
from readthedocs.builds.constants import (
    BUILD_STATUS_SUCCESS,
    SELECT_BUILD_STATUS,
)
from readthedocs.core.permissions import AdminPermission
from readthedocs.integrations.models import Integration

from ..constants import GITHUB
from ..models import RemoteOrganization, RemoteRepository
from .base import Service, SyncServiceError

log = structlog.get_logger(__name__)


class GitHubService(Service):

    """Provider service for GitHub."""

    adapter = GitHubOAuth2Adapter
    # TODO replace this with a less naive check
    url_pattern = re.compile(r'github\.com')
    vcs_provider_slug = GITHUB

    def sync_repositories(self):
        """Sync repositories from GitHub API."""
        remote_repositories = []

        try:
            repos = self.paginate('https://api.github.com/user/repos?per_page=100')
            for repo in repos:
                remote_repository = self.create_repository(repo)
                remote_repositories.append(remote_repository)
        except (TypeError, ValueError):
            log.warning('Error syncing GitHub repositories')
            raise SyncServiceError(
                'Could not sync your GitHub repositories, '
                'try reconnecting your account'
            )
        return remote_repositories

    def sync_organizations(self):
        """Sync organizations from GitHub API."""
        remote_organizations = []
        remote_repositories = []

        try:
            orgs = self.paginate('https://api.github.com/user/orgs')
            for org in orgs:
                org_details = self.get_session().get(org['url']).json()
                remote_organization = self.create_organization(org_details)
                # Add repos
                # TODO ?per_page=100
                org_repos = self.paginate(
                    '{org_url}/repos'.format(org_url=org['url']),
                )

                remote_organizations.append(remote_organization)

                for repo in org_repos:
                    remote_repository = self.create_repository(
                        repo,
                        organization=remote_organization,
                    )
                    remote_repositories.append(remote_repository)

        except (TypeError, ValueError):
            log.warning('Error syncing GitHub organizations')
            raise SyncServiceError(
                'Could not sync your GitHub organizations, '
                'try reconnecting your account'
            )

        return remote_organizations, remote_repositories

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

            repo, _ = RemoteRepository.objects.get_or_create(
                remote_id=fields['id'],
                vcs_provider=self.vcs_provider_slug
            )
            remote_repository_relation = repo.get_remote_repository_relation(
                self.user, self.account
            )

            # It's possible that a user has access to a repository from within
            # an organization without being member of that organization
            # (external contributor). In this case, the repository will be
            # listed under the ``/repos`` endpoint but not under ``/orgs``
            # endpoint. Then, when calling this method (``create_repository``)
            # we will have ``organization=None`` but we don't have to skip the
            # creation of the ``RemoteRepositoryRelation``.
            if repo.organization and organization and repo.organization != organization:
                log.debug(
                    'Not importing repository because mismatched orgs.',
                    repository=fields['name'],
                )
                return None

            if any([
                # There is an organization associated with this repository:
                # attach the organization to the repository
                organization is not None,
                # There is no organization and the repository belongs to a
                # user: removes the organization linked to the repository
                not organization and fields['owner']['type'] == 'User',
            ]):
                repo.organization = organization

            repo.name = fields['name']
            repo.full_name = fields['full_name']
            repo.description = fields['description']
            repo.ssh_url = fields['ssh_url']
            repo.html_url = fields['html_url']
            repo.private = fields['private']
            repo.vcs = 'git'
            repo.avatar_url = fields.get('owner', {}).get('avatar_url')
            repo.default_branch = fields.get('default_branch')

            if repo.private:
                repo.clone_url = fields['ssh_url']
            else:
                repo.clone_url = fields['clone_url']

            if not repo.avatar_url:
                repo.avatar_url = self.default_user_avatar_url

            repo.save()

            remote_repository_relation.admin = fields.get('permissions', {}).get('admin', False)
            remote_repository_relation.save()

            return repo

        log.debug(
            'Not importing repository because mismatched type.',
            repository=fields['name'],
        )

    def create_organization(self, fields):
        """
        Update or create remote organization from GitHub API response.

        :param fields: dictionary response of data from API
        :rtype: RemoteOrganization
        """
        organization, _ = RemoteOrganization.objects.get_or_create(
            remote_id=fields['id'],
            vcs_provider=self.vcs_provider_slug
        )
        organization.get_remote_organization_relation(
            self.user, self.account
        )

        organization.url = fields.get('html_url')
        # fields['login'] contains GitHub Organization slug
        organization.slug = fields.get('login')
        organization.name = fields.get('name')
        organization.email = fields.get('email')
        organization.avatar_url = fields.get('avatar_url')

        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url

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
        url = f'https://api.github.com/repos/{owner}/{repo}/hooks'
        log.bind(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )

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
            resp = session.get(url)
            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data:
                    if webhook_data["config"]["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            'GitHub integration updated with provider data for project.',
                        )
                        break
            else:
                log.warning(
                    'GitHub project does not exist or user does not have permissions.',
                    https_status_code=resp.status_code,
                )

        except Exception:
            log.exception('GitHub webhook Listing failed for project.')

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
        url = f'https://api.github.com/repos/{owner}/{repo}/hooks'
        log.bind(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )
        resp = None
        try:
            resp = session.post(
                url
                data=data,
                headers={'content-type': 'application/json'},
            )
            log.bind(http_status_code=resp.status_code)

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info('GitHub webhook creation successful for project.')
                return (True, resp)

            if resp.status_code in [401, 403, 404]:
                log.warning('GitHub project does not exist or user does not have permissions.')
                return (False, resp)

            # Unknown response from GitHub
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.warning(
                'GitHub webhook creation failed for project. Unknown response from GitHub.',
                debug_data=debug_data,
            )
        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception('GitHub webhook creation failed for project.')

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
        url = provider_data.get('url')
        log.bind(
            url=url,
            project_slug=project.slug,
            integration_id=integration.pk,
        )

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        try:
            resp = session.patch(
                url,
                data=data,
                headers={'content-type': 'application/json'},
            )
            log.bind(http_status_code=resp.status_code)

            # GitHub will return 200 if already synced
            if resp.status_code in [200, 201]:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info('GitHub webhook update successful for project.')
                return (True, resp)

            # GitHub returns 404 when the webhook doesn't exist. In this case,
            # we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

            # Unknown response from GitHub
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.warning(
                'GitHub webhook update failed. Unknown response from GitHub',
                debug_data=debug_data,
            )

        # Catch exceptions with request or deserializing JSON
        except (AttributeError, RequestException, ValueError):
            log.exception('GitHub webhook update failed for project.')

        integration.remove_secret()
        return (False, resp)

    def send_build_status(self, build, commit, state, link_to_build=False):
        """
        Create GitHub commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param state: build state failure, pending, or success.
        :type state: str
        :param commit: commit sha of the pull request
        :type commit: str
        :param link_to_build: If true, link to the build page regardless the state.
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
        statuses_url = f'https://api.github.com/repos/{owner}/{repo}/statuses/{commit}'

        if not link_to_build and state == BUILD_STATUS_SUCCESS:
            target_url = build.version.get_absolute_url()

        context = f'{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}'

        data = {
            'state': github_build_state,
            'target_url': target_url,
            'description': description,
            'context': context,
        }

        log.bind(
            project_slug=project.slug,
            commit_status=github_build_state,
            user_username=self.user.username,
            statuses_url=statuses_url,
        )
        resp = None
        try:
            resp = session.post(
                statuses_url,
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
            )
            log.bind(http_status_code=resp.status_code)
            if resp.status_code == 201:
                log.info("GitHub commit status created for project.")
                return True

            if resp.status_code in [401, 403, 404]:
                log.info('GitHub project does not exist or user does not have permissions.')
                return False

            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.warning(
                'GitHub commit status creation failed. Unknown GitHub response.',
                debug_data=debug_data,
            )

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception('GitHub commit status creation failed for project.')

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
                for user in AdminPermission.admins(project):
                    tokens = SocialToken.objects.filter(
                        account__user=user,
                        app__provider=cls.adapter.provider_id,
                    )
                    if tokens.exists():
                        token = tokens[0].token
        except Exception:
            log.exception('Failed to get token for project')
        return token
