"""Support code for OAuth, including webhook support."""

import structlog
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from readthedocs.integrations.models import Integration
from readthedocs.oauth.clients import get_oauth2_client
from readthedocs.oauth.services import BitbucketService
from readthedocs.oauth.services import GitHubService
from readthedocs.oauth.services import GitLabService


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
    service_class = SERVICE_MAP.get(integration.integration_type)
    if service_class is None:
        return None

    # TODO: remove after integrations without a secret are removed.
    if not integration.secret:
        integration.save()

    # If the integration's service class is different from the project's
    # git service class, we skip the update, as the webhook is not valid
    # (we can't create a GitHub webhook for a GitLab project, for example).
    if service_class != project.get_git_service_class(fallback_to_clone_url=True):
        messages.error(
            request,
            _("This integration type is not compatible with the project's Git provider."),
        )
        project.has_valid_webhook = False
        project.save()
        return False

    for service in service_class.for_project(project):
        updated = service.update_webhook(project, integration)
        if updated:
            messages.success(request, _("Webhook activated"))
            project.has_valid_webhook = True
            project.save()
            return True

    messages.error(
        request,
        _(
            "Webhook activation failed. Make sure you have the necessary permissions.",
        ),
    )
    project.has_valid_webhook = False
    project.save()
    return False


def is_access_revoked(account):
    """Check if the access token for the given account is revoked."""
    client = get_oauth2_client(account)
    if client is None:
        return True

    provider = account.get_provider()
    oauth2_adapter = provider.get_oauth2_adapter(request=provider.request)
    test_url = oauth2_adapter.profile_url
    resp = client.get(test_url)
    # NOTE: This has only been tested for GitHub,
    # check if Gitlab and Bitbucket return 401.
    if resp.status_code == 401:
        return True
    return False
