from readthedocs.settings.base import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'docs',
        'USER': 'docs',
        'PASSWORD': 'password',
        'HOST': 'database_1',
        'PORT': '5432',
    }
}


LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
LOGGING['loggers'] = {
    '': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

DEBUG = True
TEMPLATE_DEBUG = False
CELERY_ALWAYS_EAGER = False

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = False

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'redis_1:6379',
        'PREFIX': 'docs',
        'OPTIONS': {
            'DB': 1,
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
    },
}


REDIS = {
    'host': 'redis_1',
    'port': 6379,
    'db': 0,
}


BROKER_URL = 'redis://redis_1:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis_1:6379/0'


# Elasticsearch settings.
ES_HOSTS = ['search_1:9200']


SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'
SLUMBER_API_HOST = 'http://webapp:8000'
WEBSOCKET_HOST = 'localhost:8088'
PRODUCTION_DOMAIN = 'localhost:8080'

USE_SUBDOMAIN = False
NGINX_X_ACCEL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Lock builds for 10 minutes
REPO_LOCK_SECONDS = 300

# Don't re-confirm existing accounts
ACCOUNT_EMAIL_VERIFICATION = 'none'

# For testing locally.
CORS_ORIGIN_WHITELIST = (
    'localhost:8080',
    'webapp_1:8000',
)


