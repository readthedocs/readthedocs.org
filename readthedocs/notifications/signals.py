"""Custom Django signals related to notifications."""

import structlog
from allauth.account.models import EmailAddress
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.core.notifications import MESSAGE_EMAIL_VALIDATION_PENDING
from readthedocs.notifications.models import Notification
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import MESSAGE_PROJECT_SKIP_BUILDS
from readthedocs.subscriptions.notifications import MESSAGE_ORGANIZATION_DISABLED


log = structlog.get_logger(__name__)


@receiver(post_save, sender=Project)
def project_skip_builds(instance, *args, **kwargs):
    """Check if the project is ``skip`` and add/cancel the notification."""
    if instance.skip:
        Notification.objects.add(
            message_id=MESSAGE_PROJECT_SKIP_BUILDS,
            attached_to=instance,
            dismissable=False,
        )
    else:
        Notification.objects.cancel(
            message_id=MESSAGE_PROJECT_SKIP_BUILDS,
            attached_to=instance,
        )


@receiver(post_save, sender=Organization)
def organization_disabled(instance, *args, **kwargs):
    """Check if the organization is ``disabled`` and add/cancel the notification."""
    if instance.disabled:
        Notification.objects.add(
            message_id=MESSAGE_ORGANIZATION_DISABLED,
            attached_to=instance,
            dismissable=False,
        )
    else:
        Notification.objects.cancel(
            message_id=MESSAGE_ORGANIZATION_DISABLED,
            attached_to=instance,
        )


@receiver(post_save, sender=EmailAddress)
def user_email_verified(instance, *args, **kwargs):
    """Check if the primary email is validated and cancel the notification."""
    if instance.primary:
        if instance.verified:
            Notification.objects.cancel(
                attached_to=instance.user,
                message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
            )
        else:
            Notification.objects.add(
                attached_to=instance.user,
                message_id=MESSAGE_EMAIL_VALIDATION_PENDING,
                dismissable=True,
            )
