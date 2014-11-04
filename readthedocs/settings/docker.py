'''Settings used solely inside Docker build containers

Passing in environment variables to docker will override settings in this file.
Because this container should not have any access, you should never ever need
to do something like pass in passwords as environment variables.
'''

import os
import sys

from .base import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SITE_ROOT, 'docker.db'),
    }
}

BROKER_URL = None
CELERY_RESULT_BACKEND = None

SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = False
CACHE_BACKEND = 'dummy://'

SLUMBER_USERNAME = None
SLUMBER_PASSWORD = None
SLUMBER_API_HOST = None

PRODUCTION_DOMAIN = None
WEBSOCKET_HOST = None

HAYSTACK_CONNECTIONS = {'default': {}}

IMPORT_EXTERNAL_DATA = False
DONT_HIT_DB = True
NGINX_X_ACCEL_REDIRECT = True

FILE_SYNCER = 'privacy.backends.syncers.LocalSyncer'

# Set setting attributes on this module from environment variables
for (envkey, envval) in os.environ.items():
    if envkey.startswith('RTD_DOCKER_'):
        key = envkey.replace('RTD_DOCKER_', '').upper()
        globals()[key] = envval
