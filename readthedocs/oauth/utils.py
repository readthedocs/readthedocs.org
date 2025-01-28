"""Support code for OAuth, including webhook support."""

import structlog
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from readthedocs.integrations.models import Integration
from readthedocs.oauth.services import BitbucketService, GitHubService, GitLabService

log = structlog.get_logger(__name__)

SERVICE_MAP = {
    Integration.GITHUB_WEBHOOK: GitHubService,
    Integration.BITBUCKET_WEBHOOK: BitbucketService,
    Integration.GITLAB_WEBHOOK: GitLabService,
}


def update_webhook(project, integration, request=None):
    """Update a specific project integration instead of brute forcing."""
    # FIXME: this method supports ``request=None`` on its definition.
    # However, it does not work when passing ``request=None`` as
    # it uses that object without checking if it's ``None`` or not.
    service_cls = SERVICE_MAP.get(integration.integration_type)
    if service_cls is None:
        return None

    # TODO: remove after integrations without a secret are removed.
    if not integration.secret:
        integration.save()

    updated = False
    if project.remote_repository:
        remote_repository_relations = (
            project.remote_repository.remote_repository_relations.filter(
                account__isnull=False, user=request.user
            ).select_related("account")
        )

        for relation in remote_repository_relations:
            service = service_cls(request.user, relation.account)
            updated, __ = service.update_webhook(project, integration)

            if updated:
                break
    else:
        # The project was imported manually and doesn't have a RemoteRepository
        # attached. We do brute force over all the accounts registered for this
        # service
        service_accounts = service_cls.for_user(request.user)
        for service in service_accounts:
            updated, __ = service.update_webhook(project, integration)
            if updated:
                break

    if updated:
        messages.success(request, _("Webhook activated"))
        project.has_valid_webhook = True
        project.save()
        return True

    messages.error(
        request,
        _(
            "Webhook activation failed. "
            "Make sure you have the necessary permissions.",
        ),
    )
    project.has_valid_webhook = False
    project.save()
    return False
