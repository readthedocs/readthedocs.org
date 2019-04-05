"""Support code for OAuth, including webhook support."""

import logging

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from readthedocs.integrations.models import Integration
from readthedocs.oauth.services import (
    BitbucketService,
    GitHubService,
    GitLabService,
)
from readthedocs.projects.models import Project


log = logging.getLogger(__name__)

SERVICE_MAP = {
    Integration.GITHUB_WEBHOOK: GitHubService,
    Integration.BITBUCKET_WEBHOOK: BitbucketService,
    Integration.GITLAB_WEBHOOK: GitLabService,
}


def update_webhook(project, integration, request=None):
    """Update a specific project integration instead of brute forcing."""
    service_cls = SERVICE_MAP.get(integration.integration_type)
    if service_cls is None:
        return None

    updated = False
    try:
        account = project.remote_repository.account
        service = service_cls(request.user, account)
        updated, __ = service.update_webhook(project, integration)
    except Project.remote_repository.RelatedObjectDoesNotExist:
        # The project was imported manually and doesn't have a RemoteRepository
        # attached. We do brute force over all the accounts registered for this
        # service
        service_accounts = service_cls.for_user(request.user)
        for service in service_accounts:
            updated, __ = service.update_webhook(project, integration)
            if updated:
                break

    if updated:
        messages.success(request, _('Webhook activated'))
        project.has_valid_webhook = True
        project.save()
        return True
    messages.error(
        request,
        _(
            'Webhook activation failed. '
            'Make sure you have the necessary permissions.',
        ),
    )
    project.has_valid_webhook = False
    project.save()
    return False
