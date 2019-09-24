"""Local development settings for build processes. Database access is disabled."""

import os

from .base import CommunityBuildSettingsMixin
from ..dev import CommunityDevSettings


class CommunityBuildDevSettings(CommunityBuildSettingsMixin,
                                CommunityDevSettings):

    pass


CommunityBuildDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from ..local_settings import *  # noqa
    except ImportError:
        pass

# Finally, override the database settings in particular that we need to remove
# in order to quarantine the database, as well as some docker settings.
CommunityBuildDevSettings.override_settings(__name__)
