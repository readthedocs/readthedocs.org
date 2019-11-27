"""Project template tags and filters."""

from django import template

from readthedocs.projects.utils import get_projects_last_owner
from readthedocs.projects.version_handling import comparable_version

register = template.Library()


@register.filter
def sort_version_aware(versions):
    """Takes a list of versions objects and sort them using version schemes."""
    repo_type = None
    if versions:
        repo_type = versions[0].project.repo_type
    return sorted(
        versions,
        key=lambda version: comparable_version(version.verbose_name, repo_type=repo_type),
        reverse=True,
    )


@register.filter
def is_project_user(user, project):
    """Return if user is a member of project.users."""
    return user in project.users.all()


@register.filter
def projects_last_owner(user):
    """Returns projects where `user` is the last owner"""
    return get_projects_last_owner(user)
