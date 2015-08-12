import logging

from django.conf import settings
from django.db import models


logger = logging.getLogger(__name__)


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')


class GithubProjectManager(models.Manager):
    def create_from_api(self, api_json, user, organization=None,
                        privacy=DEFAULT_PRIVACY_LEVEL):
        logger.info('Trying GitHub: %s' % api_json['full_name'])
        if (
                (api_json['private'] is True and privacy == 'private') or
                (api_json['private'] is False and privacy == 'public')):
            project, created = self.get_or_create(
                full_name=api_json['full_name'],
                users__pk=user.pk,
            )
            if project.organization and project.organization != organization:
                logger.debug('Not importing %s because mismatched orgs' %
                             api_json['name'])
                return None
            else:
                project.organization = organization
            project.users.add(user)
            project.name = api_json['name']
            project.description = api_json['description']
            project.git_url = api_json['git_url']
            project.ssh_url = api_json['ssh_url']
            project.html_url = api_json['html_url']
            project.json = api_json
            project.save()
            return project
        else:
            logger.debug('Not importing %s because mismatched type' %
                         api_json['name'])


class GithubOrganizationManager(models.Manager):
    def create_from_api(self, api_json, user):
        organization, created = self.get_or_create(login=api_json.get('login'))
        organization.html_url = api_json.get('html_url')
        organization.name = api_json.get('name')
        organization.email = api_json.get('email')
        organization.json = api_json
        organization.users.add(user)
        organization.save()
        return organization


class BitbucketProjectManager(models.Manager):
    def create_from_api(self, api_json, user, organization=None,
                        privacy=DEFAULT_PRIVACY_LEVEL):
        logger.info('Trying Bitbucket: %s' % api_json['full_name'])
        if (api_json['is_private'] is True and privacy == 'private' or
                api_json['is_private'] is False and privacy == 'public'):
            project, created = self.get_or_create(
                full_name=api_json['full_name'])
            if project.organization and project.organization != organization:
                logger.debug('Not importing %s because mismatched orgs' %
                             api_json['name'])
                return None
            else:
                project.organization = organization
            project.users.add(user)
            project.name = api_json['name']
            project.description = api_json['description']
            project.git_url = api_json['links']['clone'][0]['href']
            project.ssh_url = api_json['links']['clone'][1]['href']
            project.html_url = api_json['links']['html']['href']
            project.vcs = api_json['scm']
            project.json = api_json
            project.save()
            return project
        else:
            logger.debug('Not importing %s because mismatched type' %
                         api_json['name'])


class BitbucketTeamManager(models.Manager):
    pass
