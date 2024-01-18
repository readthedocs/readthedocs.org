"""Read the Docs notifications."""

import textwrap

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import WARNING
from readthedocs.notifications.messages import Message, registry

MESSAGE_EMAIL_VALIDATION_PENDING = "core:email:validation-pending"
messages = [
    Message(
        id=MESSAGE_EMAIL_VALIDATION_PENDING,
        header=_("Email address not verified"),
        body=_(
            textwrap.dedent(
                """
            Your primary email address is not verified.
            Please <a href="{{account_email_url}}">verify it here</a>.
            """
            ).strip(),
        ),
        type=WARNING,
    ),
]


registry.add(messages)
