import logging
import json

import django.dispatch
from django.conf import settings
from django.contrib import messages
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from builds import utils as build_utils
from oauth import utils as oauth_utils

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
            session = oauth_utils.get_oauth_session(user=request.user, provider=provider)
            if provider == 'github':
                try:
                    owner, repo = build_utils.get_github_username_repo(version=None, repo_url=project.repo)
                    data = json.dumps({
                        'name': 'readthedocs',
                        'active': True,
                        'config': {'url': 'https://{domain}/github'.format(domain=settings.PRODUCTION_DOMAIN)}
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
                try:
                    owner, repo = build_utils.get_bitbucket_username_repo(version=None, repo_url=project.repo)
                    data = {
                        'type': 'POST',
                        'url': 'https://{domain}/bitbucket'.format(domain=settings.PRODUCTION_DOMAIN),
                    }
                    resp = session.post(
                        'https://api.bitbucket.org/1.0/repositories/{owner}/{repo}/services'.format(owner=owner, repo=repo),
                        data=data,
                    )
                    log.info("Creating BitBucket webhook response code: {code}".format(code=resp.status_code))
                    if resp.status_code == 200:
                        messages.success(request, _('BitBucket webhook activated'))
                except:
                    log.exception('BitBucket Hook creation failed', exc_info=True)
