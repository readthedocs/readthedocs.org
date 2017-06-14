"""Notification constants"""

from __future__ import absolute_import
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
