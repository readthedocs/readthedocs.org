# -*- coding: utf-8 -*-
"""Project notifications"""

from __future__ import absolute_import
from datetime import timedelta
from django.utils import timezone
from messages_extends.models import Message
from readthedocs.notifications import Notification
from readthedocs.notifications.constants import REQUIREMENT


class ResourceUsageNotification(Notification):

    name = 'resource_usage'
    context_object_name = 'project'
    subject = 'Builds for {{ project.name }} are using too many resources'
    level = REQUIREMENT


class DeprecatedWebhookEndpointNotification(Notification):

    """
    Notification for the usage of deprecated webhook endpoints.

    Each time that a view decorated with ``notify_deprecated_endpoint`` is hit,
    a new instance of this class is created. Then, ``.send`` is called and the
    ``SiteBackend`` will create (avoiding duplication) a site notification and
    the ``EmailBackend`` will do nothing (because of ``send_email=False``).

    Besides, a ``message_extends.models.Message`` object is created to track
    sending an email if this endpoint is hit again after ``email_period``. When,
    ``.send`` is call and the ``email_period`` was reach from the
    ``Message.created`` time we mark ``send_email=True`` in this instance and
    call the super ``.send`` method that will effectively send the email and
    mark the message as ``read=True``.
    """

    name = 'deprecated_webhook_endpoint'
    context_object_name = 'project'
    subject = 'Project {{ project.name }} is using a deprecated webhook'
    send_email = False
    email_period = timedelta(days=7)
    level = REQUIREMENT

    def __init__(self, context_object, request, user=None):
        # Each time this class is instantiated we create a new Message (it's
        # de-duplicated by using the ``message``, ``user`` and ``read`` status)
        self.message, created = Message.objects.get_or_create(
            message='{}: {}'.format(self.name, self.get_subject()),
            level=self.level,
            user=user,
            read=False,
        )

        # Mark this notification to be sent as email the first time that it's
        # created (user hits this endpoint for the first time)
        if created:
            self.send_email = True

        super(DeprecatedWebhookEndpointNotification, self).__init__(
            context_object,
            request,
            user,
        )

    def send(self, *args, **kwargs):
        if self.message.created + self.email_period < timezone.now():
            # Mark this instance to really send the email and rely on the
            # EmailBackend to effectively send the email
            self.send_email = True

            # Mark the message as read and send the email
            self.message.read = True
            self.message.save()
        super(DeprecatedWebhookEndpointNotification, self).send(*args, **kwargs)
