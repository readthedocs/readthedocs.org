from .base import *

REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ALWAYS_EAGER = False

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(SITE_ROOT, 'whoosh_index'),
    },
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'PREFIX': 'docs',
        'OPTIONS': {
            'DB': 1,
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SLUMBER_API_HOST = 'http://localhost:8000'
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")
SESSION_COOKIE_DOMAIN = None

TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
TEST_OUTPUT_VERBOSE = True
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_DIR = os.path.join(SITE_ROOT, 'xml_output')

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'
SLUMBER_API_HOST = 'http://localhost:8000'

WEBSOCKET_HOST = 'localhost:8088'

IMPORT_EXTERNAL_DATA = False
DONT_HIT_DB = False
#PRODUCTION_DOMAIN = 'readthedocs.org'
#USE_SUBDOMAIN = True


try:
    from local_settings import *
except:
    pass
