"""Slumber API client"""
from __future__ import absolute_import
import logging

from slumber import API
from requests import Session
from django.conf import settings


log = logging.getLogger(__name__)

PRODUCTION_DOMAIN = getattr(settings, 'PRODUCTION_DOMAIN', 'readthedocs.org')
USER = getattr(settings, 'SLUMBER_USERNAME', None)
PASS = getattr(settings, 'SLUMBER_PASSWORD', None)
API_HOST = getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org')


def setup_api():
    session = Session()
    session.headers.update({'Host': PRODUCTION_DOMAIN})
    api_config = {
        'base_url': '%s/api/v1/' % API_HOST,
        'session': session,
    }
    if USER and PASS:
        log.debug("Using slumber with user %s, pointed at %s", USER, API_HOST)
        session.auth = (USER, PASS)
    else:
        log.warning("SLUMBER_USERNAME/PASSWORD settings are not set")
    return API(**api_config)


api = setup_api()
