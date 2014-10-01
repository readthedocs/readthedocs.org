from django.conf import settings
from redis import Redis

redis = Redis(**settings.REDIS)

def readthedocs_processor(request):
    exports = {
        'BUILD_QUEUE_DEPTH': redis.llen('celery'),
        'PRODUCTION_DOMAIN': getattr(settings, 'PRODUCTION_DOMAIN', None),
        'USE_SUBDOMAINS': getattr(settings, 'USE_SUBDOMAINS', None),
        'GLOBAL_ANALYTICS_CODE': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
    }
    return exports
