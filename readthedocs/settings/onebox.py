from .base import *

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ALWAYS_EAGER = False
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://localhost:8983/solr',
    }
}

CACHE_BACKEND = 'memcached://localhost:11211/'
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

SLUMBER_API_HOST = 'http://localhost:8000'
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")

#PRODUCTION_URL = 'readthedocs.org'
#USE_SUBDOMAIN = True



