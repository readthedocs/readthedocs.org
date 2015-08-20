import logging
import json

import django.dispatch
from django.conf import settings
from django.contrib import messages
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds import utils as build_utils
from readthedocs.oauth import utils as oauth_utils

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
            if not session:
                break
            if provider == 'github':
                try:
                    resp = oauth_utils.add_github_webhook(session, project)
                    if resp.status_code == 201:
                        messages.success(request, _('GitHub webhook activated'))
                except:
                    log.exception('GitHub Hook creation failed', exc_info=True)
            elif provider == 'bitbucket':
                try:
                    resp = oauth_utils.add_bitbucket_webhook(session, project)
                    if resp.status_code == 200:
                        messages.success(request, _('BitBucket webhook activated'))
                except:
                    log.exception('BitBucket Hook creation failed', exc_info=True)
