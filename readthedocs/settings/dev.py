"""Local development settings, including local_settings, if present."""
from __future__ import absolute_import
import os

from .base import CommunityBaseSettings


class CommunityDevSettings(CommunityBaseSettings):

    """Common settings for local development"""

    PRODUCTION_DOMAIN = 'localhost:8000'
    WEBSOCKET_HOST = 'localhost:8088'

    @property
    def DATABASES(self):  # noqa
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(self.SITE_ROOT, 'dev.db'),
            }
        }

    DONT_HIT_DB = False

    ACCOUNT_EMAIL_VERIFICATION = 'none'
    SESSION_COOKIE_DOMAIN = None
    CACHE_BACKEND = 'dummy://'

    SLUMBER_USERNAME = 'test'
    SLUMBER_PASSWORD = 'test'  # noqa: ignore dodgy check
    SLUMBER_API_HOST = 'http://127.0.0.1:8000'
    PUBLIC_API_URL = 'http://127.0.0.1:8000'

    EXTERNAL_VERSION_URL = 'http://127.0.0.1:8000/static/external'

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ALWAYS_EAGER = True
    CELERY_TASK_IGNORE_RESULT = False

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    FILE_SYNCER = 'readthedocs.builds.syncers.LocalSyncer'

    # For testing locally. Put this in your /etc/hosts:
    # 127.0.0.1 test
    # and navigate to http://test:8000
    CORS_ORIGIN_WHITELIST = (
        'test:8000',
    )

    # Disable auto syncing elasticsearch documents in development
    ELASTICSEARCH_DSL_AUTOSYNC = False

    # Disable password validators on development
    AUTH_PASSWORD_VALIDATORS = []

    @property
    def LOGGING(self):  # noqa - avoid pep8 N802
        logging = super().LOGGING
        logging['formatters']['default']['format'] = '[%(asctime)s] ' + self.LOG_FORMAT
        # Allow Sphinx and other tools to create loggers
        logging['disable_existing_loggers'] = False
        return logging

    @property
    def INSTALLED_APPS(self):
        apps = super().INSTALLED_APPS
        apps.append('debug_toolbar')
        return apps

    @property
    def MIDDLEWARE(self):
        middlewares = list(super().MIDDLEWARE)
        middlewares.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        return middlewares

    @property
    def DOCKER_IMAGE(self):
        docker_image = super().DOCKER_IMAGE
        if getattr(self, 'DOCKER_USE_DEV_IMAGES', False):
            docker_image = docker_image.replace(
                'readthedocs/build:',
                'readthedocs/build-dev:',
            )
        return docker_image

    @property
    def DOCKER_IMAGE_SETTINGS(self):
        docker_image_settings = super().DOCKER_IMAGE_SETTINGS
        if getattr(self, 'DOCKER_USE_DEV_IMAGES', False):
            # Remap docker image setting keys
            docker_image_settings = {
                key.replace('readthedocs/build:', 'readthedocs/build-dev:'): settings
                for (key, settings)
                in docker_image_settings.items()
            }
        return docker_image_settings


if os.environ.get("DJANGO_SETTINGS_MODULE") == 'readthedocs.settings.dev':
    raise DeprecationWarning(
        "The settings module `readthedocs.settings.dev` was moved. "
        "Please use `readthedocs.settings.main.dev` instead."
    )
