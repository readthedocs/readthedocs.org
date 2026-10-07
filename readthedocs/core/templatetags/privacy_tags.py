"""Template tags to query projects by privacy."""

from django import template

from readthedocs.core.permissions import AdminPermission


register = template.Library()


@register.filter
def is_admin(user, project):
    return AdminPermission.is_admin(user, project)


@register.filter
def is_member(user, project):
    return AdminPermission.is_member(user, project)
