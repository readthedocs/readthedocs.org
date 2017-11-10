"""Local development settings, including local_settings, if present."""
from __future__ import absolute_import
import os

from .base import CommunityBaseSettings


class CommunityDevSettings(CommunityBaseSettings):

    """Settings for local development"""

    PRODUCTION_DOMAIN = '0.0.0.0:8000'
    WEBSOCKET_HOST = '0.0.0.0:8088'

    @property
    def DATABASES(self):  # noqa
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(self.SITE_ROOT, 'docker.db'),
            }
        }

    DONT_HIT_DB = False

    SESSION_COOKIE_DOMAIN = None
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            'PREFIX': 'docs',
        }
    }

    SLUMBER_USERNAME = 'test'
    SLUMBER_PASSWORD = 'test'  # noqa: ignore dodgy check
    SLUMBER_API_HOST = 'http://0.0.0.0:8000'
    PUBLIC_API_URL = 'http://0.0.0.0:8000'

    BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ALWAYS_EAGER = True

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
        },
    }

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    FILE_SYNCER = 'readthedocs.builds.syncers.LocalSyncer'

    # For testing locally. Put this in your /etc/hosts:
    # 127.0.0.1 test
    # and navigate to http://test:8000
    CORS_ORIGIN_WHITELIST = (
        'test:8000',
    )

    # Build documentation using docker image
    DOCKER_ENABLE = True

    # https://github.com/rtfd/readthedocs.org/pull/3152#issuecomment-339573168
    DOCKER_IMAGE = 'readthedocs/build:dev'

    # https://github.com/rtfd/readthedocs.org/pull/3243#issuecomment-343551486
    DOCKER_VERSION = '1.17'


    @property
    def LOGGING(self):  # noqa - avoid pep8 N802
        logging = super(CommunityDevSettings, self).LOGGING
        logging['formatters']['default']['format'] = '[%(asctime)s] ' + self.LOG_FORMAT
        # Remove double logging
        logging['loggers']['']['handlers'] = []
        return logging


CommunityDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
