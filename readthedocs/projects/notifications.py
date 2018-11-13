"""Project notifications"""

from __future__ import absolute_import
from readthedocs.notifications import Notification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class DeprecatedWebhookEndpointNotification(Notification):
    name = 'deprecated_webhook_endpoint'
    context_object_name = 'project'
    subject = 'Project {{ project.name }} is using a deprecated webhook'
    level = REQUIREMENT
