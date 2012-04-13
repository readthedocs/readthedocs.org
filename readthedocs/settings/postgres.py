from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'docs',
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': '',
        'HOST': '10.177.73.97',
        'PORT': '',
    }
}

DEBUG = False
TEMPLATE_DEBUG = False
CELERY_ALWAYS_EAGER = False

MEDIA_URL = 'http://media.readthedocs.org/'
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'
CACHE_BACKEND = 'memcached://localhost:11211/'
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://odin:8983/solr',
    }
}

SLUMBER_API_HOST = 'http://readthedocs.org'
WEBSOCKET_HOST = 'websocket.readthedocs.org:8088'


try:
    from local_settings import *
except:
    pass
