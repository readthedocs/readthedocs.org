import os.path

from .base import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SITE_ROOT, 'dev.db'),
    }
}
REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
#CELERY_ALWAYS_EAGER = False


SESSION_COOKIE_DOMAIN = None
CACHE_BACKEND = 'dummy://'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'
SLUMBER_API_HOST = 'http://localhost:8000'

WEBSOCKET_HOST = 'localhost:8088'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

IMPORT_EXTERNAL_DATA = False
DONT_HIT_DB = False
NGINX_X_ACCEL_REDIRECT = True

CELERY_ALWAYS_EAGER = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    from local_settings import *  # noqa
except:
    pass
