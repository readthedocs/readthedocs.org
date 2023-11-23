"""Project notifications."""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from messages_extends.constants import ERROR_PERSISTENT

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT


# TODO: this notification can be removed, it's just an admin action we don't really use
class ResourceUsageNotification(Notification):
    name = "resource_usage"
    context_object_name = "project"
    subject = "Builds for {{ project.name }} are using too many resources"
    level = REQUIREMENT


# TODO: migrate this communication to the new system, attached to a User
class EmailConfirmNotification(SiteNotification):
    failure_level = ERROR_PERSISTENT
    failure_message = _(
        "Your primary email address is not verified. "
        'Please <a href="{{account_email_url}}">verify it here</a>.',
    )

    def get_context_data(self):
        context = super().get_context_data()
        context.update({"account_email_url": reverse("account_email")})
        return context
