from django.conf import settings

def readthedocs_processor(request):
    exports = {
        'PRODUCTION_DOMAIN': getattr(settings, 'PRODUCTION_DOMAIN', None),
        'USE_SUBDOMAINS': getattr(settings, 'USE_SUBDOMAINS', None),
        'GLOBAL_ANALYTICS_CODE': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
    }
    return exports
