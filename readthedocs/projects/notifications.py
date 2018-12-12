"""Project notifications"""

from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _
from messages_extends.constants import ERROR_PERSISTENT

from readthedocs.notifications import Notification, SiteNotification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class EmailConfirmNotification(SiteNotification):

    failure_level = ERROR_PERSISTENT
    failure_message = _(
        'Please <a href="">add or verify your primary email address</a>.'
    )
