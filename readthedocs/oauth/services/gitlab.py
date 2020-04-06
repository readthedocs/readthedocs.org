"""OAuth utility functions."""

import json
import logging
import re

from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter
from django.conf import settings
from django.urls import reverse
from requests.exceptions import RequestException

from readthedocs.builds.constants import (
    BUILD_STATUS_SUCCESS,
    RTD_BUILD_STATUS_API_NAME,
    SELECT_BUILD_STATUS,
)
from readthedocs.builds import utils as build_utils
from readthedocs.integrations.models import Integration
from readthedocs.projects.models import Project

from ..models import RemoteOrganization, RemoteRepository
from .base import Service, SyncServiceError


try:
    from urlparse import urljoin, urlparse
except ImportError:
    from urllib.parse import urljoin, urlparse  # noqa

log = logging.getLogger(__name__)


class GitLabService(Service):

    """
    Provider service for GitLab.

    See:
     - https://docs.gitlab.com/ce/integration/oauth_provider.html
     - https://docs.gitlab.com/ce/api/oauth2.html
    """

    adapter = GitLabOAuth2Adapter
    # Just use the network location to determine if it's a GitLab project
    # because private repos have another base url, eg. git@gitlab.example.com
    url_pattern = re.compile(
        re.escape(urlparse(adapter.provider_base_url).netloc),
    )

    def _get_repo_id(self, project):
        # The ID or URL-encoded path of the project
        # https://docs.gitlab.com/ce/api/README.html#namespaced-path-encoding
        try:
            repo_id = json.loads(project.remote_repository.json).get('id')
        except Exception:
            # Handle "Manual Import" when there is no RemoteRepository
            # associated with the project. It only works with gitlab.com at the
            # moment (doesn't support custom gitlab installations)
            username, repo = build_utils.get_gitlab_username_repo(project.repo)
            if (username, repo) == (None, None):
                return None

            repo_id = '{username}%2F{repo}'.format(
                username=username,
                repo=repo,
            )
        return repo_id

    def get_next_url_to_paginate(self, response):
        return response.links.get('next', {}).get('url')

    def get_paginated_results(self, response):
        return response.json()

    def sync(self):
        """
        Sync repositories and organizations from GitLab API.

        See: https://docs.gitlab.com/ce/api/projects.html
        """
        self.sync_repositories()
        self.sync_organizations()

    def sync_repositories(self):
        repos = self.paginate(
            '{url}/api/v4/projects'.format(url=self.adapter.provider_base_url),
            per_page=100,
            archived=False,
            order_by='path',
            sort='asc',
            membership=True,
        )

        try:
            for repo in repos:
                self.create_repository(repo)
        except (TypeError, ValueError):
            log.warning('Error syncing GitLab repositories')
            raise SyncServiceError(
                'Could not sync your GitLab repositories, '
                'try reconnecting your account'
            )

    def sync_organizations(self):
        orgs = self.paginate(
            '{url}/api/v4/groups'.format(url=self.adapter.provider_base_url),
            per_page=100,
            all_available=False,
            order_by='path',
            sort='asc',
        )

        try:
            for org in orgs:
                org_obj = self.create_organization(org)
                org_repos = self.paginate(
                    '{url}/api/v4/groups/{id}/projects'.format(
                        url=self.adapter.provider_base_url,
                        id=org['id'],
                    ),
                    per_page=100,
                    archived=False,
                    order_by='path',
                    sort='asc',
                )
                for repo in org_repos:
                    self.create_repository(repo, organization=org_obj)
        except (TypeError, ValueError):
            log.warning('Error syncing GitLab organizations')
            raise SyncServiceError(
                'Could not sync your GitLab organization, '
                'try reconnecting your account'
            )

    def is_owned_by(self, owner_id):
        return self.account.extra_data['id'] == owner_id

    def create_repository(self, fields, privacy=None, organization=None):
        """
        Update or create a repository from GitLab API response.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """
        privacy = privacy or settings.DEFAULT_PRIVACY_LEVEL
        repo_is_public = fields['visibility'] == 'public'
        if privacy == 'private' or (repo_is_public and privacy == 'public'):
            try:
                repo = RemoteRepository.objects.get(
                    full_name=fields['name_with_namespace'],
                    users=self.user,
                    account=self.account,
                )
            except RemoteRepository.DoesNotExist:
                repo = RemoteRepository.objects.create(
                    full_name=fields['name_with_namespace'],
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
            repo.ssh_url = fields['ssh_url_to_repo']
            repo.html_url = fields['web_url']
            repo.private = not repo_is_public
            if repo.private:
                repo.clone_url = repo.ssh_url
            else:
                repo.clone_url = fields['http_url_to_repo']

            repo.admin = not repo_is_public
            if not repo.admin and 'owner' in fields:
                repo.admin = self.is_owned_by(fields['owner']['id'])

            repo.vcs = 'git'
            repo.account = self.account

            owner = fields.get('owner') or {}
            repo.avatar_url = (
                fields.get('avatar_url') or owner.get('avatar_url')
            )
            if not repo.avatar_url:
                repo.avatar_url = self.default_user_avatar_url

            repo.json = json.dumps(fields)
            repo.save()
            return repo
        else:
            log.info(
                'Not importing %s because mismatched type: visibility=%s',
                fields['name_with_namespace'],
                fields['visibility'],
            )

    def create_organization(self, fields):
        """
        Update or create remote organization from GitLab API response.

        :param fields: dictionary response of data from API
        :rtype: RemoteOrganization
        """
        try:
            organization = RemoteOrganization.objects.get(
                slug=fields.get('path'),
                users=self.user,
                account=self.account,
            )
        except RemoteOrganization.DoesNotExist:
            organization = RemoteOrganization.objects.create(
                slug=fields.get('path'),
                account=self.account,
            )
            organization.users.add(self.user)

        organization.name = fields.get('name')
        organization.account = self.account
        organization.url = '{url}/{path}'.format(
            url=self.adapter.provider_base_url,
            path=fields.get('path'),
        )
        organization.avatar_url = fields.get('avatar_url')
        if not organization.avatar_url:
            organization.avatar_url = self.default_user_avatar_url
        organization.json = json.dumps(fields)
        organization.save()
        return organization

    def get_webhook_data(self, repo_id, project, integration):
        """
        Get webhook JSON data to post to the API.

        See: http://doc.gitlab.com/ce/api/projects.html#add-project-hook
        """
        return json.dumps({
            'id': repo_id,
            'push_events': True,
            'tag_push_events': True,
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
            'token': integration.secret,

            # Optional
            'issues_events': False,
            'merge_requests_events': True,
            'note_events': False,
            'job_events': False,
            'pipeline_events': False,
            'wiki_events': False,
        })

    def get_provider_data(self, project, integration):
        """
        Gets provider data from GitLab Webhooks API.

        :param project: project
        :type project: Project
        :param integration: Integration for the project
        :type integration: Integration
        :returns: Dictionary containing provider data from the API or None
        :rtype: dict
        """

        if integration.provider_data:
            return integration.provider_data

        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return None

        session = self.get_session()

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
                '{url}/api/v4/projects/{repo_id}/hooks'.format(
                    url=self.adapter.provider_base_url,
                    repo_id=repo_id,
                ),
            )

            if resp.status_code == 200:
                recv_data = resp.json()

                for webhook_data in recv_data:
                    if webhook_data["url"] == rtd_webhook_url:
                        integration.provider_data = webhook_data
                        integration.save()

                        log.info(
                            'GitLab integration updated with provider data for project: %s',
                            project,
                        )
                        break
            else:
                log.info(
                    'GitLab project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

        except Exception:
            log.exception(
                'GitLab webhook Listing failed for project: %s',
                project,
            )

        return integration.provider_data

    def setup_webhook(self, project, integration=None):
        """
        Set up GitLab project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :param integration: Integration for a project
        :type integration: Integration
        :returns: boolean based on webhook set up success
        :rtype: bool
        """
        resp = None

        if not integration:
            integration, _ = Integration.objects.get_or_create(
                project=project,
                integration_type=Integration.GITLAB_WEBHOOK,
            )

        if not integration.secret:
            integration.recreate_secret()

        repo_id = self._get_repo_id(project)

        if repo_id is None:
            # Set the secret to None so that the integration can be used manually.
            integration.remove_secret()
            return (False, resp)

        data = self.get_webhook_data(repo_id, project, integration)
        session = self.get_session()
        try:
            resp = session.post(
                '{url}/api/v4/projects/{repo_id}/hooks'.format(
                    url=self.adapter.provider_base_url,
                    repo_id=repo_id,
                ),
                data=data,
                headers={'content-type': 'application/json'},
            )

            if resp.status_code == 201:
                integration.provider_data = resp.json()
                integration.save()
                log.info(
                    'GitLab webhook creation successful for project: %s',
                    project,
                )
                return (True, resp)

            if resp.status_code in [401, 403, 404]:
                log.info(
                    'Gitlab project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )

        except (RequestException, ValueError):
            log.exception(
                'GitLab webhook creation failed for project: %s',
                project,
            )
        else:
            log.error(
                'GitLab webhook creation failed for project: %s',
                project,
            )

        # Always remove secret and return False if we don't return True above
        integration.remove_secret()
        return (False, resp)

    def update_webhook(self, project, integration):
        """
        Update webhook integration.

        :param project: project to set up webhook for
        :type project: Project

        :param integration: Webhook integration to update
        :type integration: Integration

        :returns: boolean based on webhook update success, and requests Response
                  object

        :rtype: (Bool, Response)
        """
        provider_data = self.get_provider_data(project, integration)

        # Handle the case where we don't have a proper provider_data set
        # This happens with a user-managed webhook previously
        if not provider_data:
            return self.setup_webhook(project, integration)

        resp = None
        session = self.get_session()
        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return (False, resp)

        if not integration.secret:
            integration.recreate_secret()

        data = self.get_webhook_data(repo_id, project, integration)

        try:
            hook_id = provider_data.get('id')
            resp = session.put(
                '{url}/api/v4/projects/{repo_id}/hooks/{hook_id}'.format(
                    url=self.adapter.provider_base_url,
                    repo_id=repo_id,
                    hook_id=hook_id,
                ),
                data=data,
                headers={'content-type': 'application/json'},
            )

            if resp.status_code == 200:
                recv_data = resp.json()
                integration.provider_data = recv_data
                integration.save()
                log.info(
                    'GitLab webhook update successful for project: %s',
                    project,
                )
                return (True, resp)

            # GitLab returns 404 when the webhook doesn't exist. In this case,
            # we call ``setup_webhook`` to re-configure it from scratch
            if resp.status_code == 404:
                return self.setup_webhook(project, integration)

        # Catch exceptions with request or deserializing JSON
        except (AttributeError, RequestException, ValueError):
            log.exception(
                'GitLab webhook update failed for project: %s',
                project,
            )
        else:
            log.error(
                'GitLab webhook update failed for project: %s',
                project,
            )
            try:
                debug_data = resp.json()
            except ValueError:
                debug_data = resp.content
            log.debug('GitLab webhook update failure response: %s', debug_data)

        integration.remove_secret()
        return (False, resp)

    def send_build_status(self, build, commit, state):
        """
        Create GitLab commit status for project.

        :param build: Build to set up commit status for
        :type build: Build
        :param state: build state failure, pending, or success.
        :type state: str
        :param commit: commit sha of the pull request
        :type commit: str
        :returns: boolean based on commit status creation was successful or not.
        :rtype: Bool
        """
        resp = None
        session = self.get_session()
        project = build.project

        repo_id = self._get_repo_id(project)

        if repo_id is None:
            return (False, resp)

        # select the correct state and description.
        gitlab_build_state = SELECT_BUILD_STATUS[state]['gitlab']
        description = SELECT_BUILD_STATUS[state]['description']

        target_url = build.get_full_url()

        if state == BUILD_STATUS_SUCCESS:
            target_url = build.version.get_absolute_url()

        data = {
            'state': gitlab_build_state,
            'target_url': target_url,
            'description': description,
            'context': RTD_BUILD_STATUS_API_NAME
        }
        url = self.adapter.provider_base_url

        try:
            resp = session.post(
                f'{url}/api/v4/projects/{repo_id}/statuses/{commit}',
                data=json.dumps(data),
                headers={'content-type': 'application/json'},
            )

            if resp.status_code == 201:
                log.info(
                    "GitLab commit status created for project: %s, commit status: %s",
                    project,
                    gitlab_build_state,
                )
                return True

            if resp.status_code in [401, 403, 404]:
                log.info(
                    'GitLab project does not exist or user does not have '
                    'permissions: project=%s',
                    project,
                )
                return False

            return False

        # Catch exceptions with request or deserializing JSON
        except (RequestException, ValueError):
            log.exception(
                'GitLab commit status creation failed for project: %s',
                project,
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
                'GitLab commit status creation failure response: %s',
                debug_data,
            )
            return False
