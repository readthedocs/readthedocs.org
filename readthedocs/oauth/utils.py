import logging

from allauth.socialaccount.models import SocialToken

from django.conf import settings

from .models import GithubProject, GithubOrganization
from tastyapi import apiv2

log = logging.getLogger(__name__)

def make_github_project(user, org, privacy, repo_json):
    if (repo_json['private'] is True and privacy == 'private' or 
           repo_json['private'] is False and privacy == 'public'):
        project, created = GithubProject.objects.get_or_create(
            full_name=repo_json['full_name'],
        )
        if project.organization and project.organization != org:
            log.debug('Not importing %s because mismatched orgs' % repo_json['name'])
            return None
        else:
            project.organization = org
        project.users.add(user)
        project.name = repo_json['name']
        project.description = repo_json['description']
        project.git_url = repo_json['git_url']
        project.ssh_url = repo_json['ssh_url']
        project.html_url = repo_json['html_url']
        project.json = repo_json
        project.save()
        return project
    else:
        log.debug('Not importing %s because mismatched type' % repo_json['name'])

def make_github_organization(user, org_json):
    org, created = GithubOrganization.objects.get_or_create(
        login=org_json.get('login'),
    )
    org.html_url = org_json.get('html_url')
    org.name = org_json.get('name')
    org.email = org_json.get('email')
    org.json = org_json
    org.users.add(user)
    return org

def get_token_for_project(project, force_local=False):
    token = None
    try:
        if getattr(settings, 'DONT_HIT_DB', True) and not force_local:
            token = apiv2.project(project.pk).token().get()['token']
        else:
            for user in project.users.all():
                tokens = SocialToken.objects.filter(account__user__username=user.username, app__provider='github')
                if tokens.exists():
                    token = tokens[0].token
    except Exception:
        log.error('Failed to get token for user', exc_info=True)
    return token
