import slumber
import json

from django.conf import settings
USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'http://readthedocs.org')

if USER and PASS:
    print "Using slumber with Auth"
    api = slumber.API(base_url='%s/api/v1/' % API_HOST, auth=(USER, PASS))
else:
    api = slumber.API(base_url='%s/api/v1/' % API_HOST)
