# -*- coding: utf-8 -*-
"""Support for templating of notifications."""

from __future__ import absolute_import
from builtins import object
import logging
from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from django.db import models
from django.http import HttpRequest

from .backends import send_notification
from . import constants


log = logging.getLogger(__name__)


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
    success. The message is selected by using ``reason`` to get the proper
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
            self, user, success, reason=None, context_object=None,
            request=None, extra_context=None):
        self.object = context_object

        self.user = user or request.user
        # Fake the request in case the notification is instantiated from a place
        # without access to the request object (Celery task, for example)
        self.request = request or HttpRequest()
        self.request.user = user

        self.success = success
        self.reason = reason
        self.extra_context = extra_context or {}
        super(SiteNotification, self).__init__(context_object, request, user)

    def get_context_data(self):
        context = super(SiteNotification, self).get_context_data()
        context.update(self.extra_context)
        return context

    def get_message_level(self):
        if self.success:
            return self.success_level
        return self.failure_level

    def get_message(self, success):
        if success:
            message = self.success_message
        else:
            message = self.failure_message

        msg = ''  # default message in case of error
        if isinstance(message, dict):
            if self.reason:
                if self.reason in message:
                    msg = message.get(self.reason)
                else:
                    # log the error but not crash
                    log.error(
                        "Notification {} has no key '{}' for {} messages".format(
                            self.__class__.__name__,
                            self.reason,
                            'success' if self.success else 'failure',
                        ),
                    )
            else:
                log.error(
                    '{}.{}_message is a dictionary but no reason was provided'.format(
                        self.__class__.__name__,
                        'success' if self.success else 'failure',
                    ),
                )
        else:
            msg = message

        return Template(msg).render(context=Context(self.get_context_data()))

    def render(self, *args, **kwargs):  # pylint: disable=arguments-differ
        return self.get_message(self.success)
