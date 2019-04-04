"""Local development settings, including local_settings, if present."""
from __future__ import absolute_import
import os

from .base import CommunityBaseSettings


class CommunityDevSettings(CommunityBaseSettings):

    """Settings for local development"""

    PRODUCTION_DOMAIN = "localhost:8000"
    WEBSOCKET_HOST = "localhost:8088"

    MULTIPLE_APP_SERVERS = ['web']
    MULTIPLE_BUILD_SERVERS = ['build']

    @property
    def DATABASES(self):  # noqa
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "NAME": "docs_db",
                "USER": os.environ.get("DB_USER", "docs_user"),
                "PASSWORD": os.environ.get("DB_PWD", "docs_pwd"),
                "HOST": os.environ.get("DB_HOST", "database"),
                "PORT": "",
            }
        }

    DONT_HIT_DB = False

    ACCOUNT_EMAIL_VERIFICATION = "none"
    SESSION_COOKIE_DOMAIN = None
    CACHE_BACKEND = "dummy://"

    SLUMBER_USERNAME = "test"
    SLUMBER_PASSWORD = "test"  # noqa: ignore dodgy check
    SLUMBER_API_HOST = "http://web:8000"
    PUBLIC_API_URL = "http://web:8000"

    BROKER_URL = "redis://cache:6379/0"
    CELERY_RESULT_BACKEND = "redis://cache:6379/0"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ALWAYS_EAGER = False
    CELERY_TASK_IGNORE_RESULT = False

    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    FILE_SYNCER = "readthedocs.builds.syncers.RemotePuller"

    # For testing locally. Put this in your /etc/hosts:
    # 127.0.0.1 test
    # and navigate to http://test:8000
    CORS_ORIGIN_WHITELIST = ("test:8000",)

    # Disable auto syncing elasticsearch documents in development
    ELASTICSEARCH_DSL_AUTOSYNC = False

    @property
    def LOGGING(self):  # noqa - avoid pep8 N802
        logging = super().LOGGING
        logging["formatters"]["default"]["format"] = (
            "[%(asctime)s] " + self.LOG_FORMAT
        )
        # Allow Sphinx and other tools to create loggers
        logging["disable_existing_loggers"] = False
        return logging

    @property
    def INSTALLED_APPS(self):
        apps = super().INSTALLED_APPS
        apps.append("debug_toolbar")
        return apps

    @property
    def MIDDLEWARE(self):
        middlewares = list(super().MIDDLEWARE)
        middlewares.insert(
            0, "debug_toolbar.middleware.DebugToolbarMiddleware"
        )
        return middlewares


CommunityDevSettings.load_settings(__name__)

if not os.environ.get("DJANGO_SETTINGS_SKIP_LOCAL", False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
