# -*- coding: utf-8 -*-
"""Support for templating of notifications."""

from __future__ import absolute_import
from builtins import object
from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from django.db import models
from django.http import HttpRequest

from .backends import send_notification
from . import constants


class Notification(object):

    """
    An unsent notification linked to an object.

    This class provides an interface to construct notification messages by
    rendering Django templates. The ``Notification`` itself is not expected
    to be persisted by the backends.

    Call .send() to send the notification.
    """

    name = None
    context_object_name = 'object'
    level = constants.INFO
    subject = None
    user = None
    send_email = True

    def __init__(self, context_object, request, user=None):
        self.object = context_object
        self.request = request
        self.user = user
        if self.user is None:
            self.user = request.user

    def get_subject(self):
        template = Template(self.subject)
        return template.render(context=Context(self.get_context_data()))

    def get_context_data(self):
        return {
            self.context_object_name: self.object,
            'request': self.request,
            'production_uri': '{scheme}://{host}'.format(
                scheme='https', host=settings.PRODUCTION_DOMAIN,
            ),
        }

    def get_template_names(self, backend_name, source_format=constants.HTML):
        names = []
        if self.object and isinstance(self.object, models.Model):
            meta = self.object._meta  # pylint: disable=protected-access
            names.append(
                '{app}/notifications/{name}_{backend}.{source_format}'
                .format(
                    app=meta.app_label,
                    name=self.name or meta.model_name,
                    backend=backend_name,
                    source_format=source_format,
                ))
            return names
        else:
            raise AttributeError()

    def render(self, backend_name, source_format=constants.HTML):
        return render_to_string(
            template_name=self.get_template_names(
                backend_name=backend_name,
                source_format=source_format,
            ),
            context=self.get_context_data(),
        )

    def send(self):
        """
        Trigger notification send through all notification backends.

        In order to limit which backends a notification will send out from,
        override this method and duplicate the logic from
        :py:func:`send_notification`, taking care to limit which backends are
        avoided.
        """
        send_notification(self.request, self)


class SiteNotification(Notification):

    """
    Simple notification to show *only* on site messages.

    ``success_message`` and ``failure_message`` can be a simple string or a
    dictionary with different messages depending on the reason of the failure /
    success. The message is selected by using ``message_key`` to get the proper
    value.

    The notification is tied to the ``user`` and it could be sticky, persistent
    or normal --this depends on the ``success_level`` and ``failure_level``.

    .. note::

        ``send_email`` is forced to False to not send accidental emails when
        only a simple site notification is needed.
    """

    send_email = False

    success_message = None
    failure_message = None

    success_level = constants.SUCCESS_NON_PERSISTENT
    failure_level = constants.ERROR_NON_PERSISTENT

    def __init__(
            self, user, success, message_key=None, context_object=None,
            request=None):
        self.object = context_object

        self.user = user or request.user
        # Fake the request in case the notification is instantiated from a place
        # without access to the request object (Celery task, for example)
        self.request = request or HttpRequest()
        self.request.user = user

        self.success = success
        self.message_key = message_key
        super(SiteNotification, self).__init__(context_object, request, user)

    def get_message_level(self):
        if self.success:
            return self.success_level
        return self.failure_level

    def get_message(self, success):
        if success:
            message = self.success_message
        else:
            message = self.failure_message

        if isinstance(message, dict) and self.message_key:
            if self.message_key in message:
                msg = message.get(self.message_key)
            else:
                raise KeyError(
                    "Notification has no key '{}' for {} messages".format(
                        self.message_key,
                        'success' if self.success else 'failure',
                    ),
                )
        else:
            msg = message
        return msg.format(**{self.context_object_name: self.object})

    def render(self, *args, **kwargs):
        return self.get_message(self.success)
