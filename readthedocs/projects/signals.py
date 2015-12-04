"""Project signals"""

import logging

import django.dispatch
from django.contrib import messages
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from allauth.socialaccount.providers.bitbucket_oauth2.views import (
    BitbucketOAuth2Adapter)
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

from readthedocs.oauth import utils as oauth_utils
from readthedocs.oauth.constants import (OAUTH_SOURCE_BITBUCKET,
                                         OAUTH_SOURCE_GITHUB)


before_vcs = django.dispatch.Signal(providing_args=["version"])
after_vcs = django.dispatch.Signal(providing_args=["version"])

before_build = django.dispatch.Signal(providing_args=["version"])
after_build = django.dispatch.Signal(providing_args=["version"])

project_import = django.dispatch.Signal(providing_args=["project"])


log = logging.getLogger(__name__)


@receiver(project_import)
def handle_project_import(sender, **kwargs):
    """Add post-commit hook on project import"""
    project = sender
    request = kwargs.get('request')

    adapters = {
        OAUTH_SOURCE_GITHUB: GitHubOAuth2Adapter,
        OAUTH_SOURCE_BITBUCKET: BitbucketOAuth2Adapter,
    }

    for (provider, adapter) in adapters.items():
        # TODO Make this check less naive, it should check for a full URL
        if provider in project.repo:
            session = oauth_utils.get_oauth_session(user=request.user,
                                                    adapter=adapter)
            if not session:
                break
            if provider == OAUTH_SOURCE_GITHUB:
                try:
                    resp = oauth_utils.add_github_webhook(session, project)
                    if resp.status_code == 201:
                        messages.success(request, _('GitHub webhook activated'))
                # pylint: disable=bare-except
                # TODO this should be audited for exception types
                except:
                    log.exception('GitHub Hook creation failed', exc_info=True)
            elif provider == OAUTH_SOURCE_BITBUCKET:
                try:
                    resp = oauth_utils.add_bitbucket_webhook(session, project)
                    if resp.status_code == 200:
                        messages.success(request, _('BitBucket webhook activated'))
                # pylint: disable=bare-except
                # TODO this should be audited for exception types
                except:
                    log.exception('BitBucket Hook creation failed', exc_info=True)
