"""Read the Docs notifications."""

import textwrap

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.constants import TIP
from readthedocs.notifications.constants import WARNING
from readthedocs.notifications.messages import Message
from readthedocs.notifications.messages import registry


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
            Welcome to our new dashboard!
            """
        ).strip(),
        body=textwrap.dedent(
            """
            We are beginning to direct users to our new dashboard as we work to retire our legacy dashboard.
            For more information on this change and what to expect,
            <a href="https://about.readthedocs.com/blog/2024/11/rollout-of-our-new-dashboard/">read our blog post</a>.
            """
        ).strip(),
        type=TIP,
        icon_classes="fad fa-sparkles",
    ),
]


registry.add(messages)
