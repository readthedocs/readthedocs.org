"""Invitation template filters."""

from django import template

from readthedocs.invitations.models import Invitation


register = template.Library()


@register.filter
def can_revoke_invitation(user, object):
    if isinstance(object, Invitation):
        return object.can_revoke_invitation(user)
    return False
