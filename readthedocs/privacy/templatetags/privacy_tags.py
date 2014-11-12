from django import template

from ..loader import AdminPermission

from projects.models import Project

register = template.Library()


@register.filter
def is_admin(user, project):
    return AdminPermission.is_admin(user, project)


@register.simple_tag(takes_context=True)
def get_public_projects(context, user):
    projects = Project.objects.for_user_and_viewer(user=user, viewer=context['request'].user)
    context['public_projects'] = projects
    return ''
