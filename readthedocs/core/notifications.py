"""Read the Docs notifications."""

import textwrap

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import TIP, WARNING
from readthedocs.notifications.messages import Message, registry

MESSAGE_EMAIL_VALIDATION_PENDING = "core:email:validation-pending"
MESSAGE_NEW_DASHBOARD = "core:dashboard:new"
messages = [
    Message(
        id=MESSAGE_EMAIL_VALIDATION_PENDING,
        header=_("Email address not verified"),
        body=_(
            textwrap.dedent(
                """
            Your primary email address is not verified.
            Please <a href="{% url 'account_email' %}">verify it here</a>.
            """
            ).strip(),
        ),
        type=WARNING,
    ),
    Message(
        id=MESSAGE_NEW_DASHBOARD,
        # Skip translations on these because this has template logic inside the
        # translation and we don't want to push that to our translations sources.
        header=textwrap.dedent(
            """
            {% if RTD_EXT_THEME_ENABLED %}
              Welcome to our new dashboard!
            {% else %}
              Try our new dashboard!
            {% endif %}
            """
        ).strip(),
        body=textwrap.dedent(
            """
            {% if RTD_EXT_THEME_ENABLED %}
              Feel free to <a href="https://{{ PRODUCTION_DOMAIN }}/support/">contact us</a> if you have any questions or feedback.
              If you encounter any problems, you can also <a href="https://{{ url_old_dashboard }}">return to the legacy dashboard</a>.
            {% else %}
              Our <strong>new dashboard</strong> is now available!
              <a href="https://{{ url_new_dashboard }}">Try it out</a> and let us know what you think.
            {% endif %}
            """
        ).strip(),
        type=TIP,
        icon_classes="fad fa-sparkles",
        format_values={
            "url_old_dashboard": settings.PRODUCTION_DOMAIN.removeprefix("app."),
            "url_new_dashboard": f"app.{settings.PRODUCTION_DOMAIN}",
        },
    ),
]


registry.add(messages)
