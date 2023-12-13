"""Support for templating of notifications."""

import structlog
from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.template import Context, Template
from django.template.loader import render_to_string

from readthedocs.core.context_processors import readthedocs_processor
from readthedocs.core.utils import send_email

from . import constants

log = structlog.get_logger(__name__)


# TODO: remove this, it's just a quick test for QA from the console.
#
# from readthedocs.domains.notifications import PendingCustomDomainValidation
# domain = Domain.objects.get(domain='docs.humitos.com')
# project = Project.objects.get(slug='test-builds')
# user = User.objects.get(username='admin')
# n = PendingCustomDomainValidation(context_object=domain, user=user)
# n.send()


class EmailNotification:

    """
    An unsent notification linked to an object.

    This class provides an interface to construct notification messages by
    rendering Django templates and send them via email.

    Call .send() to send the email notification.
    """

    name = None
    context_object_name = "object"
    app_templates = None
    subject = None
    user = None
    extra_tags = ""

    def __init__(self, context_object, user, extra_context=None):
        self.context_object = context_object
        self.extra_context = extra_context or {}
        self.user = user

    def get_subject(self):
        template = Template(self.subject)
        return template.render(context=Context(self.get_context_data()))

    def get_context_data(self):
        context = {
            self.context_object_name: self.context_object,
            "production_uri": "{scheme}://{host}".format(
                scheme="https",
                host=settings.PRODUCTION_DOMAIN,
            ),
        }
        context.update(self.extra_context)
        context.update(readthedocs_processor(None))
        return context

    def get_template_names(self, source_format=constants.HTML):
        names = []
        if self.context_object and isinstance(self.context_object, models.Model):
            meta = self.context_object._meta
            names.append(
                "{app}/notifications/{name}_{backend}.{source_format}".format(
                    app=self.app_templates or meta.app_label,
                    name=self.name or meta.model_name,
                    backend="email",
                    source_format=source_format,
                ),
            )
            return names

        raise AttributeError("Template for this email not found.")

    def render(self, source_format=constants.HTML):
        return render_to_string(
            template_name=self.get_template_names(
                source_format=source_format,
            ),
            context=self.get_context_data(),
        )

    def send(self):
        """
        Send templated notification emails through our standard email backend.

        The content body is first rendered from an on-disk template, then passed
        into the standard email templates as a string.
        """

        template = self.get_template_names(source_format=constants.TEXT)
        template_html = self.get_template_names(source_format=constants.HTML)
        send_email(
            recipient=self.user.email,
            subject=self.get_subject(),
            template=template,
            template_html=template_html,
            context=self.get_context_data(),
        )


# NOTE: this class is replaced by the new Notification model.
class SiteNotification:

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
        self,
        user,
        success,
        reason=None,
        context_object=None,
        request=None,
        extra_context=None,
    ):
        self.object = context_object

        self.user = user or request.user
        # Fake the request in case the notification is instantiated from a place
        # without access to the request object (Celery task, for example)
        self.request = request or HttpRequest()
        self.request.user = user

        self.success = success
        self.reason = reason
        super().__init__(context_object, request, user, extra_context)

    def get_message_level(self):
        if self.success:
            return self.success_level
        return self.failure_level

    def get_message(self, success):
        if success:
            message = self.success_message
        else:
            message = self.failure_message

        msg = ""  # default message in case of error
        if isinstance(message, dict):
            if self.reason:
                if self.reason in message.keys():
                    msg = message.get(self.reason)
                else:
                    # log the error but not crash
                    log.error(
                        "Notification has no key for messages",
                        notification=self.__class__.__name__,
                        key=self.reason,
                        message="success" if self.success else "failure",
                    )
            else:
                log.error(
                    "{message} is a dictionary but no reason was provided",
                    notification=self.__class__.__name__,
                    message="success" if self.success else "failure",
                )
        else:
            msg = message

        return Template(msg).render(context=Context(self.get_context_data()))

    def render(self, *args, **kwargs):
        return self.get_message(self.success)
