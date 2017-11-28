# -*- coding: utf-8 -*-
"""OAuth utility functions."""

from __future__ import division, print_function, unicode_literals

import json
import logging
import re

from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter
from django.conf import settings
from django.core.urlresolvers import reverse
from requests.exceptions import RequestException

from readthedocs.builds import utils as build_utils
from readthedocs.integrations.models import Integration

from ..models import RemoteOrganization, RemoteRepository
from .base import DEFAULT_PRIVACY_LEVEL, Service

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
        re.escape(urlparse(adapter.provider_base_url).netloc))
    default_avatar = {
        'repo': urljoin(settings.MEDIA_URL, 'images/fa-bookmark.svg'),
        'org': urljoin(settings.MEDIA_URL, 'images/fa-users.svg'),
    }

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
            log.exception('Error syncing GitLab repositories')
            raise Exception(
                'Could not sync your GitLab repositories, try reconnecting '
                'your account')

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
            log.exception('Error syncing GitLab organizations')
            raise Exception(
                'Could not sync your GitLab organization, try reconnecting '
                'your account')

    def create_repository(
            self, fields, privacy=DEFAULT_PRIVACY_LEVEL, organization=None):
        """
        Update or create a repository from GitLab API response.

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """

        def is_owned_by(owner_id):
            return self.account.extra_data['id'] == owner_id

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
            else:
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

            # TODO: review this repo.admin logic
            repo.admin = not repo_is_public
            if not repo.admin and 'owner' in fields:
                repo.admin = is_owned_by(fields['owner']['id'])

            repo.vcs = 'git'
            repo.account = self.account

            # TODO: do we want default avatar URL?
            owner = fields.get('owner') or {}
            repo.avatar_url = (
                fields.get('avatar_url') or owner.get('avatar_url') or
                self.default_avatar['repo'])

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
        avatar = fields.get('avatar') or {}
        if avatar.get('url'):
            organization.avatar_url = '{url}/{avatar}'.format(
                url=self.adapter.provider_base_url,
                avatar=avatar.get('url'),
            )
        else:
            # TODO: do we want default avatar URL here?
            organization.avatar_url = self.default_avatar['org']

        organization.json = json.dumps(fields)
        organization.save()
        return organization

    def get_webhook_data(self, repo_id, integration, project):
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

            # Optional
            'issues_events': False,
            'merge_requests_events': False,
            'note_events': False,
            'job_events': False,
            'pipeline_events': False,
            'wiki_events': False,
        })

    def setup_webhook(self, project):
        """
        Set up GitLab project webhook for project.

        :param project: project to set up webhook for
        :type project: Project
        :returns: boolean based on webhook set up success
        :rtype: bool
        """
        session = self.get_session()
        owner, repo = build_utils.get_gitlab_username_repo(url=project.repo)
        integration, _ = Integration.objects.get_or_create(
            project=project,
            integration_type=Integration.GITLAB_WEBHOOK,
        )

        # The ID or URL-encoded path of the project
        # https://docs.gitlab.com/ce/api/README.html#namespaced-path-encoding
        repo_id = '{}%2F{}'.format(owner, repo)

        data = self.get_webhook_data(repo_id, integration, project)
        resp = None
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
        except (RequestException, ValueError):
            log.exception(
                'GitLab webhook creation failed for project: %s',
                project,
            )
        else:
            log.exception(
                'GitLab webhook creation failed for project: %s',
                project,
            )
            return (False, resp)

    def update_webhook(self, project, integration):
        # TODO: to implement
        pass

    # @classmethod
    # def get_token_for_project(cls, project, force_local=False):
    #     """Get access token for project by iterating over project users."""
    #     # TODO: why does this only target GitHub?
    #     if not getattr(settings, 'ALLOW_PRIVATE_REPOS', False):
    #         return None
    #     token = None
    #     try:
    #         if getattr(settings, 'DONT_HIT_DB', True) and not force_local:
    #             token = api.project(project.pk).token().get()['token']
    #         else:
    #             for user in project.users.all():
    #                 tokens = SocialToken.objects.filter(
    #                     account__user=user,
    #                     app__provider=cls.adapter.provider_id)
    #                 if tokens.exists():
    #                     token = tokens[0].token
    #     except Exception:
    #         log.error('Failed to get token for user', exc_info=True)
    #     return token
