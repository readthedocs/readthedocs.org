"""Read the Docs notifications."""

import textwrap

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
    # This message looks quite odd because we need to show different content in
    # the notification depending on which instance the user is on -- if the user
    # is on our legacy dashboard, we don't want a notification "Welcome to our
    # new dashboard!".
    #
    # Localization is avoided because the body has template logic inside and we
    # don't want to push that to our translations sources.
    Message(
        id=MESSAGE_NEW_DASHBOARD,
        header=textwrap.dedent(
            """
            {% if RTD_EXT_THEME_ENABLED %}
              Welcome to our new dashboard!
            {% else %}
              Our new dashboard is ready!
            {% endif %}
            """
        ).strip(),
        body=textwrap.dedent(
            """
            {% if RTD_EXT_THEME_ENABLED %}
              We are beginning to direct users to our new dashboard as we work to retire our legacy dashboard.
            {% else %}
              You are currently using our legacy dashboard, which will be retired on <time datetime="2025-03-11">March 11th, 2025</time>.
              You should <a href="//{{ SWITCH_PRODUCTION_DOMAIN }}{% url "account_login" %}">switch to our new dashboard</a> before then.
            {% endif %}
            For more information on this change and what to expect,
            <a href="https://about.readthedocs.com/blog/2024/11/rollout-of-our-new-dashboard/">read our blog post</a>.
            """
        ).strip(),
        type=TIP,
        icon_classes="fad fa-sparkles",
    ),
]


registry.add(messages)
