"""Read the Docs notifications."""

import textwrap

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import INFO, WARNING
from readthedocs.notifications.messages import Message, registry

MESSAGE_EMAIL_VALIDATION_PENDING = "core:email:validation-pending"
MESSAGE_BETA_DASHBOARD_AVAILABLE = "core:dashboard:beta-available"
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
    Message(
        id=MESSAGE_BETA_DASHBOARD_AVAILABLE,
        header=_("New beta dashboard available"),
        body=_(
            textwrap.dedent(
                """
                Our new <strong>beta dashboard</strong> is now available for testing.
                <a href="https://beta.readthedocs.org/">Give it a try</a> and send us feedback.
            """
            ).strip(),
        ),
        type=INFO,
    ),
]


registry.add(messages)
