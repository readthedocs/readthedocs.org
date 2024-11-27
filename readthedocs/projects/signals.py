"""Project signals."""


import django.dispatch
import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.projects.models import AddonsConfig, Project

log = structlog.get_logger(__name__)


before_vcs = django.dispatch.Signal()

before_build = django.dispatch.Signal()
after_build = django.dispatch.Signal()

project_import = django.dispatch.Signal()

# Used to purge files from the CDN
files_changed = django.dispatch.Signal()


@receiver(post_save, sender=Project)
def create_addons_on_new_projects(instance, *args, **kwargs):
    """Create ``AddonsConfig`` on new projects."""
    AddonsConfig.objects.get_or_create(project=instance)
