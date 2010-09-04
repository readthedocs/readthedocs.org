from .base import *
import os.path


DATABASES = {
        'default': 
                {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(SITE_ROOT, 'dev.db'),
                }
}

SESSION_COOKIE_DOMAIN = None
HAYSTACK_SOLR_URL = 'http://localhost:8983/solr'

