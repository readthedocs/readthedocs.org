"""Signals to keep the edge redirect store in sync with the database."""

import structlog
from django.conf import settings
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.projects.models import Domain
from readthedocs.redirects.models import Redirect
from readthedocs.redirects.tasks import remove_domain_from_edge
from readthedocs.redirects.tasks import sync_project_to_edge


log = structlog.get_logger(__name__)


def _enabled():
    return settings.RTD_EDGE_REDIRECTS_ENABLED


@receiver(post_save, sender=Redirect)
@receiver(post_delete, sender=Redirect)
def resync_edge_on_redirect_change(sender, instance, **kwargs):
    """Re-sync a project's redirects to the edge when one changes."""
    if _enabled():
        sync_project_to_edge.delay(instance.project_id)


@receiver(post_save, sender=Domain)
def resync_edge_on_domain_save(sender, instance, **kwargs):
    """Re-sync the project when a custom domain changes (canonical/https/host)."""
    if _enabled():
        sync_project_to_edge.delay(instance.project_id)


@receiver(post_delete, sender=Domain)
def cleanup_edge_on_domain_delete(sender, instance, **kwargs):
    """Drop the deleted host and refresh the project's canonical config."""
    if _enabled():
        remove_domain_from_edge.delay(instance.domain)
        sync_project_to_edge.delay(instance.project_id)
