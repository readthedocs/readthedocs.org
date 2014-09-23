from django import template

from ..loader import AdminPermission

register = template.Library()


@register.filter
def is_admin(user, project):
    return AdminPermission.is_admin(user, project)
