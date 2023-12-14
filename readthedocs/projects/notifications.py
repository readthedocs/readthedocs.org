"""Notifications related to projects."""

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import INFO
from readthedocs.notifications.messages import Message, registry

MESSAGE_PROJECT_SKIP_BUILDS = "project:invalid:skip-builds"
messages = [
    Message(
        id=MESSAGE_PROJECT_SKIP_BUILDS,
        header=_("Build skipped for this project"),
        body=_(
            """
            Your project is currently disabled for abuse of the system.
            Please make sure it isn't using unreasonable amounts of resources or triggering lots of builds in a short amount of time.
            Please <a href="mailto:{SUPPORT_EMAIL}">contact support</a> to get your project re-enabled.
            """
        ),
        type=INFO,
    ),
]
registry.add(messages)
