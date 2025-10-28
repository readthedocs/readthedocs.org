import os
from pathlib import Path
import textwrap

from .base import CommunityBaseSettings


class CommunityTestSettings(CommunityBaseSettings):

    """Settings for testing environment (e.g. tox)"""

    SLUMBER_API_HOST = "http://localhost:8000"

    # A bunch of our tests check this value in a returned URL/Domain
    PRODUCTION_DOMAIN = "readthedocs.org"
    PUBLIC_DOMAIN = "readthedocs.io"
    DONT_HIT_DB = False

    # Disable password validators on tests
    AUTH_PASSWORD_VALIDATORS = []

    DEBUG = False
    TEMPLATE_DEBUG = False
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ELASTICSEARCH_DSL_AUTO_REFRESH = True

    CELERY_ALWAYS_EAGER = True

    # Skip automatic detection of Docker limits for testing
    BUILD_TIME_LIMIT = 600
    BUILD_MEMORY_LIMIT = "200m"

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "PREFIX": "docs",
        }
    }

    # Random private RSA key for testing
    # $ openssl genpkey -algorithm RSA -out private-key.pem -pkeyopt rsa_keygen_bits:4096
    GITHUB_APP_PRIVATE_KEY = textwrap.dedent("""
        -----BEGIN PRIVATE KEY-----
        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
        agcfZZcGZQjnJO+V/MWnsSY4obY8Ag==
        -----END PRIVATE KEY-----
    """).strip()
    GITHUB_APP_WEBHOOK_SECRET = "secret"

    @property
    def PASSWORD_HASHERS(self):
        # Speed up tests by using a fast password hasher as the default.
        # https://docs.djangoproject.com/en/5.0/topics/testing/overview/#speeding-up-the-tests.
        return ["django.contrib.auth.hashers.MD5PasswordHasher"] + super().PASSWORD_HASHERS

    @property
    def DATABASES(self):  # noqa
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(self.SITE_ROOT, "dev.db"),
            },
            "telemetry": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(self.SITE_ROOT, "telemetry.dev.db"),
            },
        }

    @property
    def ES_INDEXES(self):  # noqa - avoid pep8 N802
        es_indexes = super(CommunityTestSettings, self).ES_INDEXES
        for index_conf in es_indexes.values():
            index_conf["name"] = "test_{}".format(index_conf["name"])

        return es_indexes

    @property
    def LOGGING(self):  # noqa - avoid pep8 N802
        logging = super().LOGGING

        logging["handlers"]["console"]["level"] = "DEBUG"
        logging["formatters"]["default"]["format"] = "[%(asctime)s] " + self.LOG_FORMAT
        # Allow Sphinx and other tools to create loggers
        logging["disable_existing_loggers"] = False
        return logging

    @property
    def STORAGES(self):
        # Attempt to fix tests using the default storage backends
        return {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
            "usercontent": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {
                    "location": Path(self.MEDIA_ROOT) / "usercontent",
                    "allow_overwrite": True,
                },
            },
        }



CommunityTestSettings.load_settings(__name__)
