"""Local setting for celery without DB access"""

import os

from .dev import CommunityDevSettings


class CeleryDevSettings(CommunityDevSettings):
    @property
    def DATABASES(self):  # noqa
        return {
            'default': {}
        }

    DONT_HIT_DB = True


CeleryDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
