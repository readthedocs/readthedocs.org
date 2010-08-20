from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'docs',
        'USER': 'postgres',                      # Not used with sqlite3.
        'PASSWORD': '',
        'HOST': 'golem',
        'PORT': '',
    }
}

try:
    from local_settings import *
except:
    pass
