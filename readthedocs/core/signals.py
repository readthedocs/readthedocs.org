"""Signal handling for core app."""

import requests
import structlog
from allauth.account.signals import email_confirmed
from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import Signal
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
from simple_history.signals import pre_create_historical_record

from readthedocs.analytics.utils import get_client_ip
from readthedocs.core.models import UserProfile
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)

webhook_github = Signal()
webhook_gitlab = Signal()
webhook_bitbucket = Signal()

pre_collectstatic = Signal()
post_collectstatic = Signal()


@receiver(email_confirmed)
def process_email_confirmed(request, email_address, **kwargs):
    """
    Steps to take after a users email address is confirmed.

    Add the user to the MailerLite onboarding group for the drip campaign,
    if they opted in at signup.
    Newsletter subscriptions happen later, see ``subscribe_active_users_to_newsletter``.
    """

    # email_address is an object
    # https://github.com/pennersr/django-allauth/blob/6315e25/allauth/account/models.py#L15
    user = email_address.user
    profile = UserProfile.objects.filter(user=user).first()
    if not profile or not profile.mailing_list or not settings.MAILERLITE_API_ONBOARDING_GROUP_URL:
        return

    # TODO: Unsubscribe users if they unset `mailing_list`.
    structlog.contextvars.bind_contextvars(
        email=email_address.email,
        user_username=user.username,
    )

    log.info("Adding user to onboarding group.")
    try:
        # TODO: migrate this signal to a Celery task since it has a `requests.post` on it.
        resp = requests.post(
            settings.MAILERLITE_API_ONBOARDING_GROUP_URL,
            json={"email": email_address.email, "resubscribe": True, "type": "active"},
            headers={"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY},
            timeout=3,  # seconds
        )
        resp.raise_for_status()
    except requests.Timeout:
        log.warning("Timeout adding user to onboarding group.")
    except Exception:  # noqa
        log.exception("Unknown error adding user to onboarding group.")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a :py:class:`UserProfile` automatically when a user is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_projects_and_organizations(sender, instance, *args, **kwargs):
    """
    Delete projects and organizations where the user is the only owner.

    We delete projects that don't belong to an organization first,
    then full organizations.
    """
    user = instance

    for project in Project.objects.single_owner(user):
        project.delete()

    for organization in Organization.objects.single_owner(user):
        organization.delete()


@receiver(pre_create_historical_record)
def add_extra_historical_fields(sender, **kwargs):
    history_instance = kwargs["history_instance"]
    if not history_instance:
        return

    history_user = kwargs["history_user"]
    if history_user:
        history_instance.extra_history_user_id = history_user.id
        history_instance.extra_history_user_username = history_user.username

    request = getattr(HistoricalRecords.context, "request", None)
    if request:
        history_instance.extra_history_ip = get_client_ip(request)
        history_instance.extra_history_browser = request.headers.get("User-Agent")
