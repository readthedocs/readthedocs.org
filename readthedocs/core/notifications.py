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
        header=_("New beta dashboard"),
        body=_(
            textwrap.dedent(
                """
                {% if RTD_EXT_THEME_ENABLED %}
                This dashboard is currently in beta,
                you can <a href="https://{{ PRODUCTION_DOMAIN }}">return to the legacy dashboard</a> if you encounter any problems.
                Feel free to <a href="https://{{ PRODUCTION_DOMAIN }}/support/">report any feedback</a> you may have.
                {% else %}
                Our new <strong>beta dashboard</strong> is now available for testing.
                <a href="https://app.{{ PRODUCTION_DOMAIN }}/">Give it a try</a> and send us feedback.
                {% endif %}
            """
            ).strip(),
        ),
        type=INFO,
    ),
]


registry.add(messages)
