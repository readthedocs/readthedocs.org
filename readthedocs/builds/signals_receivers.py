"""
Receiver signals for the Builds app.

NOTE: Done in a separate file to avoid circular imports.
"""

from itertools import groupby

import structlog
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import (
    MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES,
)


log = structlog.get_logger(__name__)


# Number of consecutive failed builds on the default version
# before we disable the project.
RTD_BUILDS_MAX_CONSECUTIVE_FAILURES = getattr(settings, "RTD_BUILDS_MAX_CONSECUTIVE_FAILURES", 50)


@receiver(post_save, sender=Build)
def update_latest_build_for_project(sender, instance, created, **kwargs):
    """When a build is created, update the latest build for the project."""
    if created:
        Project.objects.filter(pk=instance.project_id).update(
            latest_build=instance,
        )


@receiver(build_complete, sender=Build)
def disable_project_on_consecutive_failed_builds(sender, build, **kwargs):
    """
    Disable a project if it has too many consecutive failed builds on the default version.

    When a project has 50+ consecutive failed builds on the default version,
    we attach a notification to the project and disable builds (skip=True).
    This helps reduce resource consumption from projects that are not being monitored.
    """
    # Build is a dict coming from the task, not a Build instance
    if not isinstance(build, dict):
        return

    # Only check on failed builds
    if build.get("success"):
        return

    project_id = build.get("project")
    version_slug = build.get("version_slug")

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return

    # Only check for the default version
    if version_slug != project.get_default_version():
        return

    # Skip if the project is already disabled
    if project.skip:
        return

    # Count consecutive failed builds on the default version
    builds = (
        Build.objects.filter(
            project=project,
            version_slug=version_slug,
            state=BUILD_STATE_FINISHED,
        )
        .order_by("-date")
        .values_list("success", flat=True)[: RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 1]
    )
    for success, group in groupby(builds):
        consecutive_failed_builds = len(list(group))
        if success and consecutive_failed_builds > RTD_BUILDS_MAX_CONSECUTIVE_FAILURES:
            log.info(
                "Disabling project due to consecutive failed builds.",
                project_slug=project.slug,
                version_slug=version_slug,
                consecutive_failed_builds=consecutive_failed_builds,
            )

            # Disable the project
            project.skip = True
            project.save()

            # Attach notification to the project
            Notification.objects.add(
                message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES,
                attached_to=project,
                dismissable=False,
                format_values={
                    "consecutive_failed_builds": consecutive_failed_builds,
                },
            )

            # If we already detected the threshold, we can stop checking
            break
