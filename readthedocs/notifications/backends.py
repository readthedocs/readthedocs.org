"""Notification to message backends"""

from django.conf import settings
from django.contrib.messages import add_message
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
        add_message(
            request=self.request,
            message=notification.render(
                backend_name=self.name,
                source_format=HTML
            ),
            level=LEVEL_MAPPING.get(notification.level, INFO_PERSISTENT),
            extra_tags='',
            user=notification.user,
        )
