"""Project template tags and filters."""

from django import template

from readthedocs.builds.constants import INTERNAL
from readthedocs.core.permissions import AdminPermission
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
    """Checks if the user has access to the project."""
    return user in AdminPermission.members(project)


@register.simple_tag
def get_project_active_versions(project, user):
    return project.versions(manager=INTERNAL).public(user=user, only_active=True)
