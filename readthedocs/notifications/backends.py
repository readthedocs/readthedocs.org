"""Pluggable backends for the delivery of notifications.

Delivery of notifications to users depends on a list of backends configured in
Django settings. For example, they might be e-mailed to users as well as
displayed on the site.

"""

from __future__ import absolute_import
from builtins import object
from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string
from messages_extends.constants import INFO_PERSISTENT

from readthedocs.core.utils import send_email

from .constants import LEVEL_MAPPING, REQUIREMENT, HTML


def send_notification(request, notification):
    """Send notifications through all backends defined by settings

    Backends should be listed in the settings ``NOTIFICATION_BACKENDS``, which
    should be a list of class paths to be loaded, using the standard Django
    string module loader.
    """
    backends = getattr(settings, 'NOTIFICATION_BACKENDS', [])
    for cls_name in backends:
        backend = import_string(cls_name)(request)
        backend.send(notification)


class Backend(object):

    def __init__(self, request):
        self.request = request

    def send(self, notification):
        pass


class EmailBackend(Backend):

    """Send templated notification emails through our standard email backend

    The content body is first rendered from an on-disk template, then passed
    into the standard email templates as a string.
    """

    name = 'email'

    def send(self, notification):
        if notification.level >= REQUIREMENT:
            send_email(
                recipient=notification.user.email,
                subject=notification.get_subject(),
                template='core/email/common.txt',
                template_html='core/email/common.html',
                context={
                    'content': notification.render(self.name, source_format=HTML),
                },
                request=self.request,
            )


class SiteBackend(Backend):

    """Add messages through Django messages application

    This uses persistent messageing levels provided by :py:mod:`message_extends`
    and stores persistent messages in the database.
    """

    name = 'site'

    def send(self, notification):
        # Instead of calling the standard messages.add method, this instead
        # manipulates the storage directly. This is because we don't have a
        # request object and need to mock one out to fool the message storage
        # into saving a message for a separate user.
        cls_name = settings.MESSAGE_STORAGE
        cls = import_string(cls_name)
        req = HttpRequest()
        setattr(req, 'session', '')
        storage = cls(req)
        storage.add(
            level=LEVEL_MAPPING.get(notification.level, INFO_PERSISTENT),
            message=notification.render(
                backend_name=self.name,
                source_format=HTML
            ),
            extra_tags='',
            user=notification.user,
        )
