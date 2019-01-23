# -*- coding: utf-8 -*-

"""Notification constants."""

from messages_extends import constants as message_constants


TEXT = 'txt'
HTML = 'html'

INFO = 0
WARNING = 1
REQUIREMENT = 2
ERROR = 3

LEVEL_MAPPING = {
    INFO: message_constants.INFO_PERSISTENT,
    WARNING: message_constants.WARNING_PERSISTENT,
    REQUIREMENT: message_constants.WARNING_PERSISTENT,
    ERROR: message_constants.ERROR_PERSISTENT,
}

# Message levels to save the message into the database and mark as read
# immediately after retrieved (one-time shown message)
DEBUG_NON_PERSISTENT = 100
INFO_NON_PERSISTENT = 101
SUCCESS_NON_PERSISTENT = 102
WARNING_NON_PERSISTENT = 103
ERROR_NON_PERSISTENT = 104

NON_PERSISTENT_MESSAGE_LEVELS = (
    DEBUG_NON_PERSISTENT,
    INFO_NON_PERSISTENT,
    SUCCESS_NON_PERSISTENT,
    WARNING_NON_PERSISTENT,
    ERROR_NON_PERSISTENT,
)
