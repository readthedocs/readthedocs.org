# -*- coding: utf-8 -*-

"""Simple client to access our API with Slumber credentials."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

import requests
from django.conf import settings
from requests_toolbelt.adapters import host_header_ssl
from rest_framework.renderers import JSONRenderer
from slumber import API, serialize

log = logging.getLogger(__name__)

PRODUCTION_DOMAIN = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org')
USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)


class DrfJsonSerializer(serialize.JsonSerializer):

    """Additional serialization help from the DRF renderer"""

    key = 'json-drf'

    def dumps(self, data):
        """Used to be able to render datetime objects."""
        return JSONRenderer().render(data)


def setup_api():
    session = requests.Session()
    if API_HOST.startswith('https'):
        # Only use the HostHeaderSSLAdapter for HTTPS connections
        adapter_class = host_header_ssl.HostHeaderSSLAdapter
    else:
        adapter_class = requests.adapters.HTTPAdapter

    session.mount(
        API_HOST,
        adapter_class(max_retries=3),
    )
    session.headers.update({'Host': PRODUCTION_DOMAIN})
    api_config = {
        'base_url': '%s/api/v2/' % API_HOST,
        'serializer': serialize.Serializer(
            default='json-drf',
            serializers=[
                serialize.JsonSerializer(),
                DrfJsonSerializer(),
            ],
        ),
        'session': session,
    }
    if USER and PASS:
        log.debug(
            'Using slumber v2 with user %s, pointed at %s',
            USER,
            API_HOST,
        )
        session.auth = (USER, PASS)
    else:
        log.warning('SLUMBER_USERNAME/PASSWORD settings are not set')
    return API(**api_config)


api = setup_api()
