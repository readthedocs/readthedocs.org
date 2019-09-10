"""Local setting for celery build workers (without DB access)"""

import os

from ..base import CommunityDevSettings


# Load ``local_settings`` first to avoid ``DATABASES`` being override
if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from ..local_settings import *  # noqa
    except ImportError:
        pass


class CeleryDevSettings(CommunityDevSettings):
    @property
    def DATABASES(self):  # noqa
        return {
            'default': {}
        }

    DONT_HIT_DB = True


CeleryDevSettings.load_settings(__name__)
