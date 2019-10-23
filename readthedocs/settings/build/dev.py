"""Local development settings for build processes. Database access is disabled."""

import os

from .base import CommunityBuildSettingsMixin
from ..dev import CommunityDevSettings


class CommunityBuildDevSettings(CommunityBuildSettingsMixin,
                                CommunityDevSettings):

    pass


CommunityBuildDevSettings.load_settings(__name__)
