"""Local development settings for the dashboard and web workers"""

import os

from .base import CommunityMainSettingsMixin
from ..dev import CommunityDevSettings


class CommunityMainDevSettings(CommunityMainSettingsMixin,
                               CommunityDevSettings):

    pass


CommunityMainDevSettings.load_settings(__name__)
