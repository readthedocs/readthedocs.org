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
    ELASTICSEARCH_DSL_AUTOSYNC = False
    ELASTICSEARCH_DSL_AUTO_REFRESH = True

    CELERY_ALWAYS_EAGER = True

    # Skip automatic detection of Docker limits for testing
    DOCKER_LIMITS = {'memory': '200m', 'time': 600}

    STRIPE_PUBLISHABLE = 'pk_test_'
    STRIPE_SECRET = 'sk_test_'

    @property
    def ES_INDEXES(self):  # noqa - avoid pep8 N802
        es_indexes = super(CommunityTestSettings, self).ES_INDEXES
        for index_conf in es_indexes.values():
            index_conf['name'] = "test_{}".format(index_conf['name'])

        return es_indexes

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
