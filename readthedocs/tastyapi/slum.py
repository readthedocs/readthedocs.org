import slumber
import json

from django.conf import settings
USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)

if USER and PASS:
    api = slumber.API(base_url='http://readthedocs.org/api/v1/', auth=(USER, PASS))
else:
    api = slumber.API(base_url='http://readthedocs.org/api/v1/')
