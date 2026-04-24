"""Notifications related to custom domains."""

import textwrap

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import INFO
from readthedocs.notifications.email import EmailNotification
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry


class PendingCustomDomainValidation(EmailNotification):
    app_templates = "domains"
    context_object_name = "domain"
    name = "pending_domain_configuration"
    subject = "Pending configuration of custom domain {{ domain.domain }}"


MESSAGE_DOMAIN_VALIDATION_PENDING = "project:domain:validation-pending"
MESSAGE_DOMAIN_VALIDATION_EXPIRED = "project:domain:validation-expired"
messages = [
    Message(
        id=MESSAGE_DOMAIN_VALIDATION_PENDING,
        header=_("Pending configuration of custom domain: {{domain}}"),
        body=_(
            textwrap.dedent(
                """
            The configuration of your custom domain <code>{{domain}}</code> is pending.
            Go to the <a href="{{domain_url}}">domain page</a> and follow the instructions to complete it.
            """
            ).strip(),
        ),
        type=INFO,
    ),
    # TODO: the custom domain expired notification requires a periodic task to
    # remove the old notification and create a new one pointing to this
    # ``message_id``
    Message(
        id=MESSAGE_DOMAIN_VALIDATION_EXPIRED,
        header=_("Validation of custom domain expired: {{domain}}"),
        body=_(
            textwrap.dedent(
                """
            The validation period of your custom domain <code>{{domain}}</code> has ended.
            Go to the <a href="{{domain_url}}">domain page</a> and click on "Save" to restart the process.
            """
            ).strip(),
        ),
        type=INFO,
    ),
]
registry.add(messages)
