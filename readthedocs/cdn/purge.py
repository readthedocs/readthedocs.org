import logging

from django.conf import settings

log = logging.getLogger(__name__)

CDN_SERVICE = getattr(settings, 'CDN_SERVICE', None)
CDN_USERNAME = getattr(settings, 'CDN_USERNAME', None)
CDN_KEY = getattr(settings, 'CDN_KEY', None)
CDN_SECET = getattr(settings, 'CDN_SECET', None)
CDN_ID = getattr(settings, 'CDN_ID', None)


if CDN_USERNAME and CDN_KEY and CDN_SECET and CDN_ID and CDN_SERVICE == 'maxcdn':
    from maxcdn import MaxCDN
    api = MaxCDN(CDN_USERNAME, CDN_KEY, CDN_SECET)

    def purge(files):
        return api.purge(CDN_ID, files)
else:
    def purge(files):
        log.error("CDN not configured, can't purge files")
