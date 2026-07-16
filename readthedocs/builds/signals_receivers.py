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


@receiver(post_save, sender=Build)
def set_valid_clone_after_successful_build(sender, instance, created, **kwargs):
    """
    Set the valid_clone flag to True after a successful build.

    This is used to indicate that the project has been successfully built at least once.
    """
    build = instance
    if build.finished and build.success:
        project = build.project
        if not project.valid_clone:
            project.valid_clone = True
            project.save()
