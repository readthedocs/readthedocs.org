"""Support code for OAuth, including webhook support."""

import structlog

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
