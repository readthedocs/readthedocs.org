"""Endpoint to generate footer HTML."""


import structlog

from readthedocs.builds.constants import LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.version_handling import (
    highest_version,
    parse_version_failsafe,
)

log = structlog.get_logger(__name__)


def get_version_compare_data(project, base_version=None, user=None):
    """
    Retrieve metadata about the highest version available for this project.

    :param base_version: We assert whether or not the base_version is also the
                         highest version in the resulting "is_highest" value.
    """
    if not project.show_version_warning or (base_version and base_version.is_external):
        return {"is_highest": False}

    versions_qs = Version.internal.public(project=project, user=user).filter(
        built=True, active=True
    )

    # Take preferences over tags only if the project has at least one tag
    if versions_qs.filter(type=TAG).exists():
        versions_qs = versions_qs.filter(type=TAG)

    # Optimization
    versions_qs = versions_qs.select_related("project")

    highest_version_obj, highest_version_comparable = highest_version(
        versions_qs,
    )
    ret_val = {
        "project": str(highest_version_obj),
        "version": str(highest_version_comparable),
        "is_highest": True,
    }
    if highest_version_obj:
        # Never link to the dashboard,
        # users reading the docs may don't have access to the dashboard.
        ret_val["url"] = highest_version_obj.get_absolute_url()
        ret_val["slug"] = highest_version_obj.slug
    if base_version and base_version.slug != LATEST:
        try:
            base_version_comparable = parse_version_failsafe(
                base_version.verbose_name,
            )
            if base_version_comparable:
                # This is only place where is_highest can get set. All error
                # cases will be set to True, for non- standard versions.
                ret_val["is_highest"] = (
                    base_version_comparable >= highest_version_comparable
                )
            else:
                ret_val["is_highest"] = True
        except (Version.DoesNotExist, TypeError):
            ret_val["is_highest"] = True
    return ret_val
