from allauth.socialaccount.adapter import get_adapter
from django import forms, template

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
