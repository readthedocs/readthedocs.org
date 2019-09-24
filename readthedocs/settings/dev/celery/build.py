"""Local setting for celery build workers (without DB access)"""

import os

from readthedocs.core.settings import Settings

from ..base import CommunityDevSettings


class CommunityDevCelerySettings(Settings):

    """
    This settings class is empty except for the settings we are resetting

    Instead of inheriting, like other settings classes do, we are using this
    class without inheritance, so that we can reset settings and use the same
    pattern as the other settings modules.
    """

    @property
    def DATABASES(self):  # noqa
        return {
            'default': {}
        }

    DONT_HIT_DB = True


CommunityDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from ..local_settings import *  # noqa
    except ImportError:
        pass

# Last, load overrides to database settings
CommunityDevCelerySettings.load_settings(__name__)
