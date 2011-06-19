from .base import *
import os.path


DATABASES = {
        'default':
                {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(SITE_ROOT, 'dev.db'),
                }
}
REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}



SESSION_COOKIE_DOMAIN = None
HAYSTACK_SOLR_URL = 'http://localhost:8983/solr'
CACHE_BACKEND = 'dummy://'


try:
    from local_settings import *
except:
    pass
