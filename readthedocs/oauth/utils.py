"""Support code for OAuth, including webhook support."""

import structlog
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.bitbucket_oauth2.provider import BitbucketOAuth2Provider
from django.db.models import Q

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


def get_bitbucket_accounts_without_account_id():
    """
    Return Bitbucket accounts that don't have an ``account_id`` saved.

    These accounts can't be matched on login, since allauth identifies
    Bitbucket accounts by their ``account_id``.
    """
    return SocialAccount.objects.filter(
        # The key isn't present, or it's present with a null value.
        Q(extra_data__account_id__isnull=True) | Q(extra_data__account_id=None),
        provider=BitbucketOAuth2Provider.id,
    )


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
