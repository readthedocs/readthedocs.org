import slumber
import logging

from django.conf import settings

log = logging.getLogger(__name__)

USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org')

if USER and PASS:
    log.debug("Using slumber with user %s, pointed at %s" % (USER, API_HOST))
    api = slumber.API(base_url='%s/api/v1/' % API_HOST, auth=(USER, PASS))
else:
    log.warning("SLUMBER_USERNAME/PASSWORD settings are not set")
    api = slumber.API(base_url='%s/api/v1/' % API_HOST)
