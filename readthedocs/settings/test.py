import os.path

from .sqlite import *  # noqa

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

SLUMBER_USERNAME = 'test'
SLUMBER_PASSWORD = 'test'
SLUMBER_API_HOST = 'http://localhost:8000'
# A bunch of our tests check this value in a returned URL/Domain
PRODUCTION_DOMAIN = 'readthedocs.org'

try:
    from local_settings import *  # noqa
except:
    pass
