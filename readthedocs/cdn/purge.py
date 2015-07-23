import logging

from django.conf import settings

log = logging.getLogger(__name__)

CDN_SERVICE = getattr(settings, 'CDN_SERVICE')
CDN_USERNAME = getattr(settings, 'CDN_USERNAME')
CDN_KEY = getattr(settings, 'CDN_KEY')
CDN_SECET = getattr(settings, 'CDN_SECET')
CDN_ID = getattr(settings, 'CDN_ID')


def purge(files):
    log.error("CDN not configured, can't purge files")

if CDN_USERNAME and CDN_KEY and CDN_SECET and CDN_ID:
    if CDN_SERVICE == 'maxcdn':
        from maxcdn import MaxCDN as cdn_service
        api = cdn_service(CDN_USERNAME, CDN_KEY, CDN_SECET)

        def purge(files):
            return api.purge(CDN_ID, files)
