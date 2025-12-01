"""
Receiver signals for the Builds app.

NOTE: Done in a separate file to avoid circular imports.
"""

import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.builds.models import Build
from readthedocs.builds.signals import build_complete
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


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
    Trigger a Celery task to check for consecutive failed builds.

    When a project has more than RTD_BUILDS_MAX_CONSECUTIVE_FAILURES consecutive failed builds on the default version,
    we attach a notification to the project and disable builds (skip=True).
    This helps reduce resource consumption from projects that are not being monitored.
    """
    from readthedocs.builds.tasks import check_and_disable_project_for_consecutive_failed_builds

    # Build is a dict coming from the task, not a Build instance
    if not isinstance(build, dict):
        return

    # Only check on failed builds
    if build.get("success"):
        return

    project_id = build.get("project")
    version_slug = build.get("version_slug")

    if not project_id or not version_slug:
        return

    # Trigger the Celery task to check and disable the project
    check_and_disable_project_for_consecutive_failed_builds.delay(
        project_id=project_id,
        version_slug=version_slug,
    )
