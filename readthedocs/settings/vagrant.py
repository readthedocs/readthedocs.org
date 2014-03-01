# Vagrant development settings

from .base import *  # noqa


REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'docs',
        'USER': 'docs',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ALWAYS_EAGER = False

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'PREFIX': 'docs',
        'OPTIONS': {
            'DB': 1,
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
        },
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")
SESSION_COOKIE_DOMAIN = 'localhost'
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_DOMAIN = 'localhost'
CSRF_COOKIE_SECURE = False

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'
SLUMBER_API_HOST = 'http://localhost:8000'

WEBSOCKET_HOST = 'localhost:8088'

IMPORT_EXTERNAL_DATA = False
DONT_HIT_DB = False
PRODUCTION_DOMAIN = 'localhost'
USE_SUBDOMAIN = False
