import logging

from slumber import API, serialize
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser


log = logging.getLogger(__name__)

USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org')


class DrfJsonSerializer(serialize.JsonSerializer):
    '''Additional serialization help from the DRF parser/renderer'''
    key = 'json-drf'

    def loads(self, data):
        return JSONParser().parse(data)

    def dumps(self, data):
        return JSONRenderer().render(data)


def setup_api():
    api_config = {
        'base_url': '%s/api/v2/' % API_HOST,
        'serializer': serialize.Serializer(
            default='json-drf',
            serializers=[
                serialize.JsonSerializer(),
                DrfJsonSerializer(),
            ]
        )
    }
    if USER and PASS:
        log.debug("Using slumber v2 with user %s, pointed at %s", USER, API_HOST)
        api_config['auth'] = (USER, PASS)
    else:
        log.warning("SLUMBER_USERNAME/PASSWORD settings are not set")
    return API(**api_config)


api = setup_api()
