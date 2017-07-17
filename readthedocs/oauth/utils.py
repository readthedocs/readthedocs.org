"""Support code for OAuth, including webhook support."""
from __future__ import absolute_import
import logging

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from readthedocs.integrations.models import Integration
from readthedocs.oauth.services import registry, GitHubService, BitbucketService

log = logging.getLogger(__name__)

SERVICE_MAP = {
    Integration.GITHUB_WEBHOOK: GitHubService,
    Integration.BITBUCKET_WEBHOOK: BitbucketService,
}


def attach_webhook(project, request=None):
    """Add post-commit hook on project import

    This is a brute force approach to adding a webhook to a repository. We try
    all accounts until we set up a webhook. This should remain around for legacy
    connections -- that is, projects that do not have a remote repository them
    and were not set up with a VCS provider.
    """
    for service_cls in registry:
        if service_cls.is_project_service(project):
            service = service_cls
            break
    else:
        messages.error(
            request,
            _('Webhook activation failed. '
              'There are no connected services for this project.')
        )
        return None

    user_accounts = service.for_user(request.user)
    for account in user_accounts:
        success, __ = account.setup_webhook(project)
        if success:
            messages.success(request, _('Webhook activated'))
            project.has_valid_webhook = True
            project.save()
            return True
    # No valid account found
    if user_accounts:
        messages.error(
            request,
            _('Webhook activation failed. Make sure you have permissions to set it.')
        )
    else:
        messages.error(
            request,
            _('No accounts available to set webhook on. '
                'Please connect your {network} account.'.format(
                    network=service.adapter(request).get_provider().name
                ))
        )
    return False


def update_webhook(project, integration, request=None):
    """Update a specific project integration instead of brute forcing"""
    service_cls = SERVICE_MAP.get(integration.integration_type)
    if service_cls is None:
        return None
    account = project.remote_repository.account
    service = service_cls(request.user, account)
    updated, __ = service.update_webhook(project, integration)
    if updated:
        messages.success(request, _('Webhook activated'))
        project.has_valid_webhook = True
        project.save()
        return True
    messages.error(
        request,
        _('Webhook activation failed. '
            'Make sure you have the necessary permissions.')
    )
    project.has_valid_webhook = False
    project.save()
    return False
