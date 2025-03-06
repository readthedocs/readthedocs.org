"""Invitations related signals."""

import structlog
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


# pylint: disable=unused-argument
@receiver(pre_delete, sender=Project)
@receiver(pre_delete, sender=Organization)
@receiver(pre_delete, sender=Team)
def delete_related_invitations(sender, instance, **kwargs):
    """
    Delete related invitations of an object.

    Generic foreign keys don't have a way to cascade delete,
    so we need to do it manually.
    """
    invitations = Invitation.objects.for_object(instance)
    log.info(
        "Deleting related invitations.",
        object_type=sender.__name__.lower(),
        object_id=instance.pk,
        count=invitations.count(),
    )
    invitations.delete()
