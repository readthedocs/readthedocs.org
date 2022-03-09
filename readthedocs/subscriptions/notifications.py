"""Organization level notifications."""

from django.urls import reverse
from messages_extends.constants import WARNING_PERSISTENT

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT
from readthedocs.organizations.models import Organization
from readthedocs.subscriptions.constants import DISABLE_AFTER_DAYS


class SubscriptionNotificationMixin:

    """Force to read templates from the subscriptions app."""

    app_templates = 'subscriptions'


class TrialEndingNotification(SubscriptionNotificationMixin, Notification):

    """Trial is ending, nudge user towards subscribing."""

    name = 'trial_ending'
    context_object_name = 'organization'
    subject = 'Your trial is ending soon'
    level = REQUIREMENT

    @classmethod
    def for_organizations(cls):
        advanced_plan_subscription_trial_ending = (
            Organization.objects.subscription_trial_ending()
            .created_days_ago(days=24)
        )
        trial_plan_subscription_trial_ending = (
            Organization.objects.subscription_trial_plan_ending()
            .created_days_ago(days=24)
        )
        return advanced_plan_subscription_trial_ending | trial_plan_subscription_trial_ending


class SubscriptionRequiredNotification(SubscriptionNotificationMixin, Notification):

    """Trial has ended, push user into subscribing."""

    name = 'subscription_required'
    context_object_name = 'organization'
    subject = 'We hope you enjoyed your trial of Read the Docs!'
    level = REQUIREMENT

    @classmethod
    def for_organizations(cls):
        advanced_plan_subscription_trial_ended = (
            Organization.objects.subscription_trial_ended()
            .created_days_ago(days=30)
        )
        trial_plan_subscription_ended = (
            Organization.objects.subscription_trial_plan_ended()
            .created_days_ago(days=30)
        )
        return advanced_plan_subscription_trial_ended | trial_plan_subscription_ended


class SubscriptionEndedNotification(SubscriptionNotificationMixin, Notification):

    """
    Subscription has ended days ago.

    Notify the customer that the Organization will be disabled *soon* if the
    subscription is not renewed for the organization.
    """

    name = 'subscription_ended'
    context_object_name = 'organization'
    subject = 'Your subscription to Read the Docs has ended'
    level = REQUIREMENT

    days_after_end = 5

    @classmethod
    def for_organizations(cls):
        organizations = Organization.objects.disable_soon(
            days=cls.days_after_end,
            exact=True,
        )
        return organizations


class OrganizationDisabledNotification(SubscriptionEndedNotification):

    """
    Subscription has ended a month ago.

    Notify the user that the organization will be disabled soon. After this
    notification is sent, we are safe to disable the organization since the
    customer was notified twice.
    """

    name = 'organization_disabled'
    subject = 'Your Read the Docs organization will be disabled soon'

    days_after_end = DISABLE_AFTER_DAYS


class OrganizationDisabledSiteNotification(SubscriptionNotificationMixin, SiteNotification):

    success_message = 'The organization "{{ object.name }}" is currently disabled. You need to <a href="{{ url }}">renew your subscription</a> to keep using Read the Docs.'  # noqa
    success_level = WARNING_PERSISTENT

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'url': reverse(
                'subscription_detail',
                args=[self.object.slug],
            ),
        })
        return context
