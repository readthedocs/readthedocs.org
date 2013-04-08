from django.conf import settings


def readthedocs_processor(request):
    exports = {
        'PRODUCTION_DOMAIN': getattr(settings, 'PRODUCTION_DOMAIN', None),
        'USE_SUBDOMAINS': getattr(settings, 'USE_SUBDOMAINS', None),
    }
    return exports
