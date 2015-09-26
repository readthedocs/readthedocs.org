import logging

from django.conf import settings

log = logging.getLogger(__name__)

CDN_SERVICE = getattr(settings, 'CDN_SERVICE', None)
CDN_USERNAME = getattr(settings, 'CDN_USERNAME', None)
CDN_KEY = getattr(settings, 'CDN_KEY', None)
CDN_SECRET = getattr(settings, 'CDN_SECRET', None)

if CDN_USERNAME and CDN_KEY and CDN_SECRET and CDN_SERVICE == 'maxcdn':
    from maxcdn import MaxCDN
    api = MaxCDN(CDN_USERNAME, CDN_KEY, CDN_SECRET)

    def purge(id, files):
        return api.purge(id, files)
else:
    def purge(id, files):
        log.error("CDN not configured, can't purge files")
