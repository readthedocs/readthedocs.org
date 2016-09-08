"""Notification to message backends"""

from django.contrib.messages.storage.base import Message
from messages_extends.constants import INFO_PERSISTENT

class Backend(object):

    def send(self, request, notification):
        pass


class EmailBackend(Backend):

    name = 'email'


class SiteBackend(Backend):

    name = 'site'

    def send(self, request, notification):
        message = Message(
            level=INFO_PERSISTENT,
            message=notification.render(
                backend_name=self.name,
                source_format='html'
            ),
            extra_tags='',
        )
        if hasattr(request, '_messages'):
            request._messages.process_message(message)
