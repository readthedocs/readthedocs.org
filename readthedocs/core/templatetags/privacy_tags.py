# -*- coding: utf-8 -*-

"""Template tags to query projects by privacy."""

from django import template
from django.db.models import Exists, OuterRef, Subquery, Prefetch

from readthedocs.builds.models import Build
from readthedocs.core.permissions import AdminPermission
from readthedocs.projects.models import Project


register = template.Library()


@register.filter
def is_admin(user, project):
    return AdminPermission.is_admin(user, project)


@register.simple_tag(takes_context=True)
def get_public_projects(context, user):
    # Creates a Subquery object which returns the latest builds 'id'.
    # Used for optimization purpose.
    subquery = Subquery(
        Build.objects.filter(
            project=OuterRef('project_id')).values_list('id', flat=True)[:1]
    )
    # Filters the latest builds of projects.
    latest_build = Prefetch('builds', Build.objects.filter(
        pk__in=subquery), to_attr='_latest_build'
    )
    # 'Exists()' checks if the project has any good builds.
    projects = Project.objects.for_user_and_viewer(
        user=user,
        viewer=context['request'].user,
    ).prefetch_related('users', latest_build).annotate(
        _good_build=Exists(
            Build.objects.filter(success=True, project=OuterRef('pk')))
    )
    context['public_projects'] = projects
    return ''
