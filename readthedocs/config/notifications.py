"""Notifications related to Read the Docs YAML config file."""

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import ERROR
from readthedocs.notifications.messages import Message, registry

from .config import ConfigError

messages = [
    Message(
        id=ConfigError.GENERIC,
        header=_("There was an unexpected problem in your config file"),
        body=_(
            """
            There was an unexpected problem in your config file.
            Make sure the encoding is correct.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ConfigError.DEFAULT_PATH_NOT_FOUND,
        header=_("Config file not found at default path"),
        body=_(
            """
            No default configuration file found at repository's root.
            """
        ),
        type=ERROR,
    ),
]
registry.add(messages)
