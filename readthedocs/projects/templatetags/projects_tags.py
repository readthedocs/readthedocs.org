# -*- coding: utf-8 -*-

"""Project template tags and filters."""

from django import template

from readthedocs.projects.version_handling import comparable_version


register = template.Library()


@register.filter
def sort_version_aware(versions):
    """Takes a list of versions objects and sort them using version schemes."""
    return sorted(
        versions,
        key=lambda version: comparable_version(version.verbose_name),
        reverse=True,
    )


@register.filter
def is_project_user(user, project):
    """Return if user is a member of project.users."""
    return user in project.users.all()

@register.assignment_tag
def get_project_admin_url(project_pk):
    """Returns the admin url for the given project's pk."""
    return '/admin/projects/project/{}/'.format(project_pk) 
