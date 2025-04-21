from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django import forms
from django import template

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.oauth.utils import is_access_revoked as utils_is_access_revoked


register = template.Library()


@register.filter
def can_be_disconnected(account):
    """
    Check if a social account can be disconnected.

    This is used to disable the disconnect button for certain social accounts.
    """
    adapter = get_adapter()
    try:
        adapter.validate_disconnect(account=account, accounts=[])
        return True
    except forms.ValidationError:
        return False


@register.filter
def is_access_revoked(account):
    """Check if access to the account is revoked."""
    return utils_is_access_revoked(account)


@register.filter
def has_github_app_account(account):
    """Check if there is a GitHub App account matching this account."""
    if account.provider != GitHubProvider.id:
        return False

    return account.user.socialaccount_set.filter(
        provider=GitHubAppProvider.id,
        uid=account.uid,
    ).exists()
