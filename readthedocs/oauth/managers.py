import logging
import json
import re

from django.conf import settings
from django.db import models

from readthedocs.privacy.loader import RelatedUserManager

from .constants import OAUTH_SOURCE_GITHUB, OAUTH_SOURCE_BITBUCKET


log = logging.getLogger(__name__)


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')


class RemoteRepositoryManager(RelatedUserManager):

    """Model managers for remote repositories"""

    def create_from_github_api(self, api_json, user, organization=None,
                               privacy=DEFAULT_PRIVACY_LEVEL):
        if (
                (privacy == 'private') or
                (api_json['private'] is False and privacy == 'public')):
            project, created = self.get_or_create(
                full_name=api_json['full_name'],
                users__pk=user.pk,
                source=OAUTH_SOURCE_GITHUB,
            )
            if project.organization and project.organization != organization:
                log.debug('Not importing %s because mismatched orgs' %
                          api_json['name'])
                return None
            else:
                project.organization = organization
            project.users.add(user)
            project.name = api_json['name']
            project.description = api_json['description']
            project.ssh_url = api_json['ssh_url']
            project.html_url = api_json['html_url']
            project.private = api_json['private']
            if project.private:
                project.clone_url = api_json['ssh_url']
            else:
                project.clone_url = api_json['clone_url']
            project.admin = api_json.get('permissions', {}).get('admin', False)
            project.vcs = 'git'
            project.source = OAUTH_SOURCE_GITHUB
            project.avatar_url = api_json.get('owner', {}).get('avatar_url')
            project.json = json.dumps(api_json)
            project.save()
            return project
        else:
            log.debug('Not importing %s because mismatched type' %
                      api_json['name'])

    def create_from_bitbucket_api(self, api_json, user, organization=None,
                                  privacy=DEFAULT_PRIVACY_LEVEL):
        """Update or create a repository from Bitbucket

        This looks up existing repositories based on the full repository name,
        that is the username and repository name.

        .. note::
            The :py:data:`admin` property is not set during creation, as
            permissions are not part of the returned repository data from
            Bitbucket.
        """
        if (api_json['is_private'] is True and privacy == 'private' or
                api_json['is_private'] is False and privacy == 'public'):
            project, created = self.get_or_create(
                full_name=api_json['full_name'],
                source=OAUTH_SOURCE_BITBUCKET,
            )
            if project.organization and project.organization != organization:
                log.debug('Not importing %s because mismatched orgs' %
                          api_json['name'])
                return None
            else:
                project.organization = organization
            project.users.add(user)
            project.name = api_json['name']
            project.description = api_json['description']
            project.private = api_json['is_private']
            project.clone_url = api_json['links']['clone'][0]['href']
            project.ssh_url = api_json['links']['clone'][1]['href']
            if project.private:
                project.clone_url = project.ssh_url
            project.html_url = api_json['links']['html']['href']
            project.vcs = api_json['scm']
            project.source = OAUTH_SOURCE_BITBUCKET

            avatar_url = api_json['links']['avatar']['href'] or ''
            project.avatar_url = re.sub(r'\/16\/$', r'/32/', avatar_url)

            project.json = json.dumps(api_json)
            project.save()
            return project
        else:
            log.debug('Not importing %s because mismatched type' %
                      api_json['name'])


class RemoteOrganizationManager(RelatedUserManager):

    def create_from_github_api(self, api_json, user):
        organization, created = self.get_or_create(
            slug=api_json.get('login'),
            source=OAUTH_SOURCE_GITHUB,
        )
        organization.html_url = api_json.get('html_url')
        organization.name = api_json.get('name')
        organization.email = api_json.get('email')
        organization.avatar_url = api_json.get('avatar_url')
        organization.json = json.dumps(api_json)
        organization.source = OAUTH_SOURCE_GITHUB
        organization.users.add(user)
        organization.save()
        return organization

    def create_from_bitbucket_api(self, api_json, user):
        organization, created = self.get_or_create(
            slug=api_json.get('username'),
            source=OAUTH_SOURCE_BITBUCKET,
        )
        organization.name = api_json.get('display_name')
        organization.email = api_json.get('email')
        organization.avatar_url = api_json['links']['avatar']['href']
        organization.html_url = api_json['links']['html']['href']
        organization.json = json.dumps(api_json)
        organization.source = OAUTH_SOURCE_BITBUCKET
        organization.users.add(user)
        organization.save()
        return organization
