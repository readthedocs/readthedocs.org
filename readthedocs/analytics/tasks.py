"""Tasks for Read the Docs' analytics"""

from __future__ import absolute_import

from django.conf import settings

from readthedocs import get_version
from readthedocs.worker import app

from .utils import send_to_analytics


DEFAULT_PARAMETERS = {
    'v': '1',               # analytics version (always 1)
    'aip': '1',             # anonymize IP
    'tid': settings.GLOBAL_ANALYTICS_CODE,

    # User data
    'uip': None,            # User IP address
    'ua': None,             # User agent

    # Application info
    'an': 'Read the Docs',
    'av': get_version(),    # App version
}


@app.task(queue='web')
def analytics_pageview(pageview_data):
    """
    Send a pageview to Google Analytics

    :see: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    :param kwargs: pageview parameters to send to GA
    """
    data = {
        't': 'pageview',
        'dl': None,         # URL of the pageview (required)
        'dt': None,         # Title of the page
    }
    data.update(DEFAULT_PARAMETERS)
    data.update(pageview_data)
    send_to_analytics(data)


@app.task(queue='web')
def analytics_event(event_data):
    """
    Send an analytics event to Google Analytics

    :see: https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide#event
    :param kwargs: event parameters to send to GA
    """
    data = {
        't': 'event',       # GA event - don't change
        'ec': None,         # Event category (required)
        'ea': None,         # Event action (required)
        'el': None,         # Event label
        'ev': None,         # Event value (numeric)
    }
    data.update(DEFAULT_PARAMETERS)
    data.update(event_data)
    send_to_analytics(data)
