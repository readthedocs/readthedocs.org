"""Organization level notifications."""


from djstripe import models as djstripe

from readthedocs.notifications import EmailNotification
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
            .prefetch_related("customer__rtd_organization")
        )


class SubscriptionRequiredNotification(
    SubscriptionNotificationMixin, EmailNotification
):

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


class OrganizationDisabledNotification(
    SubscriptionNotificationMixin, EmailNotification
):

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


# TODO: migrate this to the new system
#
# class OrganizationDisabledSiteNotification(
#     SubscriptionNotificationMixin, SiteNotification
# ):
#     success_message = 'The organization "{{ object.name }}" is currently disabled. You need to <a href="{{ url }}">renew your subscription</a> to keep using Read the Docs.'  # noqa
#     success_level = WARNING_PERSISTENT

#     def get_context_data(self):
#         context = super().get_context_data()
#         context.update(
#             {
#                 "url": reverse(
#                     "subscription_detail",
#                     args=[self.object.slug],
#                 ),
#             }
#         )
#         return context
