from __future__ import absolute_import
import os

from .dev import CommunityDevSettings


class CommunityTestSettings(CommunityDevSettings):

    SLUMBER_USERNAME = 'test'
    SLUMBER_PASSWORD = 'test'
    SLUMBER_API_HOST = 'http://localhost:8000'

    # A bunch of our tests check this value in a returned URL/Domain
    PRODUCTION_DOMAIN = 'readthedocs.org'
    GROK_API_HOST = 'http://localhost:8888'

    DEBUG = False
    TEMPLATE_DEBUG = False

    @property
    def LOGGING(self):  # noqa - avoid pep8 N802
        logging = super(CommunityDevSettings, self).LOGGING
        return logging


CommunityTestSettings.load_settings(__name__)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'PREFIX': 'docs',
    }
}

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        from .local_settings import *  # noqa
    except ImportError:
        pass
