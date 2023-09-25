import os

from .base import CommunityBaseSettings


class CommunityTestSettings(CommunityBaseSettings):

    """Settings for testing environment (e.g. tox)"""

    SLUMBER_API_HOST = "http://localhost:8000"

    # A bunch of our tests check this value in a returned URL/Domain
    PRODUCTION_DOMAIN = "readthedocs.org"
    DONT_HIT_DB = False

    # Disable password validators on tests
    AUTH_PASSWORD_VALIDATORS = []

    DEBUG = False
    TEMPLATE_DEBUG = False
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ELASTICSEARCH_DSL_AUTO_REFRESH = True

    CELERY_ALWAYS_EAGER = True

    # Skip automatic detection of Docker limits for testing
    DOCKER_LIMITS = {"memory": "200m", "time": 600}

    STRIPE_PUBLISHABLE = "pk_test_"
    STRIPE_SECRET = "sk_test_"

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "PREFIX": "docs",
        }
    }

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


CommunityTestSettings.load_settings(__name__)
