import logging
import json

import django.dispatch
from django.contrib import messages
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from allauth.socialaccount.models import SocialToken
from requests_oauthlib import OAuth1Session, OAuth2Session

from builds import utils as build_utils

before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])


log = logging.getLogger(__name__)


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """
    Add post-commit hook on project import.
    """

    project = sender
    request = kwargs.get('request')

    for provider in ['github', 'bitbucket']:
        if provider in project.repo:
            for user in project.users.all():
                tokens = SocialToken.objects.filter(account__user__username=user.username, app__provider=provider)
            for token in tokens:

                if provider == 'github':
                    session = OAuth2Session(
                        client_id=token.app.client_id,
                        token={
                            'access_token': str(token.token),
                            'token_type': 'bearer'
                        }
                    )
                    try:
                        owner, repo = build_utils.get_github_username_repo(version=None, repo_url=project.repo)
                        data = json.dumps({
                            'name': 'readthedocs',
                            'active': True,
                            'config': {'url': 'https://readthedocs.org/github'}
                        })
                        resp = session.post(
                            'https://api.github.com/repos/{owner}/{repo}/hooks'.format(owner=owner, repo=repo),
                            data=data,
                            headers={'content-type': 'application/json'}
                        )
                        log.info("Creating GitHub webhook response code: {code}".format(code=resp.status_code))
                        if resp.status_code == 201:
                            messages.success(request, _('GitHub webhook activated'))
                    except:
                        log.exception('GitHub Hook creation failed', exc_info=True)
                elif provider == 'bitbucket':
                    session = OAuth1Session(
                        token.app.client_id,
                        client_secret=token.app.secret,
                        resource_owner_key=token.token,
                        resource_owner_secret=token.token_secret
                    )
                    try:
                        owner, repo = build_utils.get_bitbucket_username_repo(version=None, repo_url=project.repo)
                        data = {
                            'type': 'Read the Docs',
                        }
                        resp = session.post(
                            'https://api.bitbucket.org/1.0/repositories/{owner}/{repo}/services'.format(owner=owner, repo=repo),
                            data=data,
                        )
                        log.info("Creating BitBucket webhook response code: {code}".format(code=resp.status_code))
                        if resp.status_code == 201:
                            messages.success(request, _('BitBucket webhook activated'))
                    except:
                        log.exception('BitBucket Hook creation failed', exc_info=True)
