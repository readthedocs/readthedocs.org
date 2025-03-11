"""Email notifications."""

import structlog
from django.conf import settings
from django.db import models
from django.template import Context
from django.template import Template
from django.template.loader import render_to_string

from readthedocs.core.context_processors import readthedocs_processor
from readthedocs.core.utils import send_email

from . import constants


log = structlog.get_logger(__name__)


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
