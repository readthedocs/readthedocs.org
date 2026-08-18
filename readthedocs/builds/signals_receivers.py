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


# TODO: this should be moved to an API call done after the build is completed.
@receiver(post_save, sender=Build)
def update_is_uploaded_for_version(sender, instance, created, **kwargs):
    """
    When a successful build via the upload API is completed, update the version.

    .. note::

       This isn't 100% accurate, as an old build could be saved again,
       and the version would be marked as uploaded even if the latest build isn't uploaded.
    """
    build = instance
    if build.version and build.finished and build.success and build.is_uploaded:
        version = instance.version
        version.is_uploaded = True
        version.save(update_fields=["is_uploaded"])
