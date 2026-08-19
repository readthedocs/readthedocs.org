"""
Receiver signals for the Builds app.

NOTE: Done in a separate file to avoid circular imports.
"""

import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.builds.models import Build
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


@receiver(post_save, sender=Build)
def update_latest_build_for_project(sender, instance, created, **kwargs):
    """When a build is created, update the latest build for the project."""
    if created:
        Project.objects.filter(pk=instance.project_id).update(
            latest_build=instance,
        )
