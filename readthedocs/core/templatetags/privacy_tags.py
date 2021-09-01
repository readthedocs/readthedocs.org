"""Template tags to query projects by privacy."""

from django import template
from django.db.models import Exists, OuterRef

from readthedocs.builds.models import Build
from readthedocs.core.permissions import AdminPermission
from readthedocs.projects.models import Project

register = template.Library()


@register.filter
def is_admin(user, project):
    return AdminPermission.is_admin(user, project)


@register.filter
def is_member(user, project):
    return AdminPermission.is_member(user, project)


@register.filter
def projects_admin(user, privacy_level=None):
    """List all projects where user is admin."""
    query = Project.objects.for_admin_user(user)
    if privacy_level:
        query = query.filter(privacy_level=privacy_level)
    return query


@register.simple_tag(takes_context=True)
def get_public_projects(context, user):
    # 'Exists()' checks if the project has any good builds.
    projects = Project.objects.for_user_and_viewer(
        user=user,
        viewer=context['request'].user,
    ).prefetch_latest_build().annotate(
        _good_build=Exists(
            Build.internal.filter(success=True, project=OuterRef('pk')))
    )
    context['public_projects'] = projects
    return ''
