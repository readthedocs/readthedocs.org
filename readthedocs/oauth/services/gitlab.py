"""OAuth utility functions"""

import logging
import json
import re

from django.conf import settings
from requests.exceptions import RequestException
from allauth.socialaccount.models import SocialToken
from allauth.socialaccount.providers.gitlab.views import GitLabOAuth2Adapter

from readthedocs.restapi.client import api

from ..models import RemoteOrganization, RemoteRepository
from .base import Service, DEFAULT_PRIVACY_LEVEL


log = logging.getLogger(__name__)


class GitLabService(Service):
    """Provider service for GitLab"""

    adapter = GitLabOAuth2Adapter
    url_pattern = re.compile(re.escape(adapter.provider_base_url))

    def paginate(self, url, **kwargs):
        """Combines return from GitLab pagination. GitLab uses
        LinkHeaders, see: http://www.w3.org/wiki/LinkHeader

        :param url: start url to get the data from.
        :param kwargs: optional parameters passed to .get() method

        See http://doc.gitlab.com/ce/api/README.html#pagination
        """
        resp = self.get_session().get(url, data=kwargs)
        result = resp.json()
        next_url = resp.links.get('next', {}).get('url')
        if next_url:
            result.extend(self.paginate(next_url, **kwargs))
        return result

    def sync(self):
        """Sync repositories from GitLab API"""
        org = None
        repos = self.paginate(
            '{url}/api/v3/projects'.format(url=self.adapter.provider_base_url),
            per_page=100,
            order_by='path',
            sort='asc'
        )
        for repo in repos:
            # Skip archived repositories
            if repo.get('archived', False):
                continue
            if not org or org.slug != repo['namespace']['id']:
                org = self.create_organization(repo['namespace'])

            self.create_repository(repo, organization=org)

    def create_repository(self, fields, privacy=DEFAULT_PRIVACY_LEVEL,
                          organization=None):
        """Update or create a repository from GitLab API response

        :param fields: dictionary of response data from API
        :param privacy: privacy level to support
        :param organization: remote organization to associate with
        :type organization: RemoteOrganization
        :rtype: RemoteRepository
        """
        # See: http://doc.gitlab.com/ce/api/projects.html#projects
        repo_is_public = fields['visibility_level'] == 20

        def is_owned_by(owner_id):
            return self.account.extra_data['id'] == owner_id

        if privacy == 'private' or (repo_is_public and privacy == 'public'):
            try:
                repo = RemoteRepository.objects.get(
                    full_name=fields['name'],
                    users=self.user,
                    account=self.account,
                )
            except RemoteRepository.DoesNotExist:
                repo = RemoteRepository.objects.create(
                    full_name=fields['name'],
                    account=self.account,
                )
                repo.users.add(self.user)

            if repo.organization and repo.organization != organization:
                log.debug('Not importing %s because mismatched orgs' %
                          fields['name'])
                return None
            else:
                repo.organization = organization
            repo.name = fields['name']
            repo.full_name = fields['name_with_namespace']
            repo.description = fields['description']
            repo.ssh_url = fields['ssh_url_to_repo']
            repo.html_url = fields['web_url']
            repo.private = not fields['public']
            repo.clone_url = fields['http_url_to_repo']
            repo.admin = not repo_is_public
            if not repo.admin and organization:
                repo.admin = is_owned_by(fields['owner']['id'])
            repo.vcs = 'git'
            repo.account = self.account
            repo.avatar_url = fields.get('avatar_url')
            repo.json = json.dumps(fields)
            repo.save()
            return repo
        else:
            log.info(
                'Not importing {0} because mismatched type: public={1}'.format(
                    fields['name_with_namespace'],
                    fields['public'],
                )
            )

    def create_organization(self, fields):
        """Update or create remote organization from GitLab API response

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
            url=self.adapter.provider_base_url, path=fields.get('path')
        )
        if fields.get('avatar'):
            organization.avatar_url = '{url}/{avatar}'.format(
                url=self.adapter.provider_base_url,
                avatar=fields['avatar']['url'],
            )
        organization.json = json.dumps(fields)
        organization.save()
        return organization

    def setup_webhook(self, project):
        """Set up GitLab project webhook for project

        :param project: project to set up webhook for
        :type project: Project
        :returns: boolean based on webhook set up success
        :rtype: bool
        """
        session = self.get_session()

        # See: http://doc.gitlab.com/ce/api/projects.html#add-project-hook
        data = json.dumps({
            'id': 'readthedocs',
            'push_events': True,
            'issues_events': False,
            'merge_requests_events': False,
            'note_events': False,
            'tag_push_events': True,
            'url': 'https://{0}/gitlab'.format(settings.PRODUCTION_DOMAIN),
        })
        resp = None
        try:
            repositories = RemoteRepository.objects.filter(
                clone_url=project.vcs_repo().repo_url
            )
            assert repositories
            repo_id = repositories[0].get_serialized()['id']
            resp = session.post(
                '{url}/api/v3/projects/{repo_id}/hooks'.format(
                    url=self.adapter.provider_base_url,
                    repo_id=repo_id,
                ),
                data=data,
                headers={'content-type': 'application/json'}
            )
            if resp.status_code == 201:
                log.info('GitLab webhook creation successful for project: %s',  # noqa
                         project)
                return True
        except (AssertionError,  RemoteRepository.DoesNotExist) as ex:
            log.error('GitLab remote repository not found', exc_info=ex)
        except RequestException as ex:
            pass
        else:
            ex = False

        log.error('GitLab webhook creation failed for project: %s',  # noqa
                  project, exc_info=ex)

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
