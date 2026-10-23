"""
Receiver signals for the Builds app.

NOTE: Done in a separate file to avoid circular imports.
"""

import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


@receiver(post_save, sender=Build)
def update_latest_build_for_project(sender, instance, created, **kwargs):
    """
    When a build is created, update the latest build for the project.

    Builds from pull request versions are skipped,
    so ``latest_build`` matches what the dashboard shows as the last build
    (see ``Project.latest_internal_build``).
    """
    if not created:
        return

    version = instance.version
    if version and version.type == EXTERNAL:
        return

    Project.objects.filter(pk=instance.project_id).update(
        latest_build=instance,
    )
