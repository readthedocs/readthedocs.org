"""Organization level notifications."""

import textwrap

from django.utils.translation import gettext_noop as _
from djstripe import models as djstripe

from readthedocs.notifications.constants import INFO
from readthedocs.notifications.email import EmailNotification
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry
from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.constants import DISABLE_AFTER_DAYS


class SubscriptionNotificationMixin:
    """Force to read templates from the subscriptions app."""

    app_templates = "subscriptions"
    context_object_name = "organization"


class TrialEndingNotification(SubscriptionNotificationMixin, EmailNotification):
    """Trial is ending, nudge user towards subscribing."""

    name = "trial_ending"
    subject = "Your trial is ending soon"

    @staticmethod
    def for_subscriptions():
        return (
            djstripe.Subscription.readthedocs.trial_ending()
            .created_days_ago(24)
            .select_related("customer__rtd_organization")
        )


class SubscriptionRequiredNotification(SubscriptionNotificationMixin, EmailNotification):
    """Trial has ended, push user into subscribing."""

    name = "subscription_required"
    subject = "We hope you enjoyed your trial of Read the Docs!"


class SubscriptionEndedNotification(SubscriptionNotificationMixin, EmailNotification):
    """
    Subscription has ended.

    Notify the customer that the Organization will be disabled *soon* if the
    subscription is not renewed for the organization.
    """

    name = "subscription_ended"
    subject = "Your subscription to Read the Docs has ended"


class OrganizationDisabledNotification(SubscriptionNotificationMixin, EmailNotification):
    """
    Subscription has ended a month ago.

    Notify the user that the organization will be disabled soon. After this
    notification is sent, we are safe to disable the organization since the
    customer was notified twice.
    """

    name = "organization_disabled"
    subject = "Your Read the Docs organization will be disabled soon"

    days_after_end = DISABLE_AFTER_DAYS

    @classmethod
    def for_organizations(cls):
        organizations = Organization.objects.disable_soon(
            days=cls.days_after_end,
            exact=True,
        )
        return organizations


MESSAGE_ORGANIZATION_DISABLED = "organization:disabled"
messages = [
    Message(
        id=MESSAGE_ORGANIZATION_DISABLED,
        header=_("Your organization has been disabled"),
        body=_(
            textwrap.dedent(
                """
            The organization "{{instance.slug}}" is currently disabled. You need to <a href="{% url 'subscription_detail' instance.slug %}">renew your subscription</a> to keep using Read the Docs
            """
            ).strip(),
        ),
        type=INFO,
    ),
]
registry.add(messages)
