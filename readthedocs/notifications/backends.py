"""Notification to message backends"""

from django.conf import settings
from django.contrib.messages import add_message
from django.utils.module_loading import import_string
from messages_extends.constants import INFO_PERSISTENT

from readthedocs.core.utils import send_email

from .constants import LEVEL_MAPPING, REQUIREMENT


def send_notification(request, notification):
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

    name = 'email'

    def send(self, notification):
        if notification.level >= REQUIREMENT:
            send_email(
                recipient=notification.user.email,
                subject=notification.get_subject(),
                template='core/email/common.txt',
                template_html='core/email/common.html',
                context={
                    'content': notification.render(self.name, source_format='html'),
                },
                request=self.request,
            )


class SiteBackend(Backend):

    name = 'site'

    def send(self, notification):
        add_message(
            request=self.request,
            message=notification.render(
                backend_name=self.name,
                source_format='html'
            ),
            level=LEVEL_MAPPING.get(notification.level, INFO_PERSISTENT),
            extra_tags='',
        )
