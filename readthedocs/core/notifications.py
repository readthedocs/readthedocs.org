"""Read the Docs notifications."""

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import WARNING
from readthedocs.notifications.messages import Message, registry

MESSAGE_EMAIL_VALIDATION_PENDING = "core:email:validation-pending"
messages = [
    Message(
        id=MESSAGE_EMAIL_VALIDATION_PENDING,
        header=_("Email address not verified"),
        body=_(
            """
            Your primary email address is not verified.
            Please <a href="{account_email_url}">verify it here</a>.
            """
        ),
        type=WARNING,
    ),
]


registry.add(messages)
