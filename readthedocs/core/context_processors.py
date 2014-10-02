from django.conf import settings
from redis import Redis, ConnectionError

redis = Redis(**settings.REDIS)

def readthedocs_processor(request):
    try:
        queue_length = redis.llen('celery')
    except ConnectionError:
        queue_length = None

    exports = {
        'BUILD_QUEUE_DEPTH': queue_length,
        'PRODUCTION_DOMAIN': getattr(settings, 'PRODUCTION_DOMAIN', None),
        'USE_SUBDOMAINS': getattr(settings, 'USE_SUBDOMAINS', None),
        'GLOBAL_ANALYTICS_CODE': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
    }
    return exports
