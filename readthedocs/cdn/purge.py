import logging

from django.conf import settings

log = logging.getLogger(__name__)

CDN_SERVICE = getattr(settings, 'CDN_SERVICE', None)
CDN_USERNAME = getattr(settings, 'CDN_USERNAME', None)
CDN_KEY = getattr(settings, 'CDN_KEY', None)
CDN_SECRET = getattr(settings, 'CDN_SECRET', None)


def chunks(in_list, chunk_size):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(in_list), chunk_size):
        yield in_list[i:i + chunk_size]

if CDN_USERNAME and CDN_KEY and CDN_SECRET and CDN_SERVICE == 'maxcdn':
    from maxcdn import MaxCDN
    api = MaxCDN(CDN_USERNAME, CDN_KEY, CDN_SECRET)

    def purge(id, files):
        # We can only purge up to 250 files per request
        for chunk in chunks(files, 200):
            return api.purge(id, chunk)
else:
    def purge(id, files):
        log.error("CDN not configured, can't purge files")
