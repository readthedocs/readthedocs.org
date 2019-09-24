"""Local development settings for the dashboard and web workers"""

import os

from .base import CommunityMainSettingsMixin
from ..dev import CommunityDevSettings


class CommunityMainDevSettings(CommunityMainSettingsMixin,
                               CommunityDevSettings):

    pass


CommunityMainDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from ..local_settings import *  # noqa
    except ImportError:
        pass
