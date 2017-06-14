"""Simple client to access our API with Slumber credentials."""

from __future__ import absolute_import
import logging

from slumber import API, serialize
from requests import Session
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser


log = logging.getLogger(__name__)

PRODUCTION_DOMAIN = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org')
USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)


class DrfJsonSerializer(serialize.JsonSerializer):

    """Additional serialization help from the DRF parser/renderer"""

    key = 'json-drf'

    def loads(self, data):
        return JSONParser().parse(data)

    def dumps(self, data):
        return JSONRenderer().render(data)


def setup_api():
    session = Session()
    session.headers.update({'Host': PRODUCTION_DOMAIN})
    api_config = {
        'base_url': '%s/api/v2/' % API_HOST,
        'serializer': serialize.Serializer(
            default='json-drf',
            serializers=[
                serialize.JsonSerializer(),
                DrfJsonSerializer(),
            ]
        ),
        'session': session,
    }
    if USER and PASS:
        log.debug("Using slumber v2 with user %s, pointed at %s", USER, API_HOST)
        session.auth = (USER, PASS)
    else:
        log.warning("SLUMBER_USERNAME/PASSWORD settings are not set")
    return API(**api_config)


api = setup_api()
