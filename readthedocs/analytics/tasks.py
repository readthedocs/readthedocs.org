# -*- coding: utf-8 -*-

"""Tasks for Read the Docs' analytics."""

from django.conf import settings

import readthedocs
from readthedocs.worker import app

from .utils import send_to_analytics


DEFAULT_PARAMETERS = {
    'v': '1',  # analytics version (always 1)
    'aip': '1',  # anonymize IP
    'tid': settings.GLOBAL_ANALYTICS_CODE,

    # User data
    'uip': '',  # User IP address
    'ua': '',  # User agent

    # Application info
    'an': 'Read the Docs',
    'av': readthedocs.__version__,  # App version
}


@app.task(queue='web')
def analytics_pageview(url, title=None, **kwargs):
    """
    Send a pageview to Google Analytics.

    :see: https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    :param url: the URL of the pageview
    :param title: the title of the page being viewed
    :param kwargs: extra pageview parameters to send to GA
    """
    data = {
        't': 'pageview',
        'dl': url,  # URL of the pageview (required)
        'dt': title,  # Title of the page
    }
    data.update(DEFAULT_PARAMETERS)
    data.update(kwargs)
    send_to_analytics(data)


@app.task(queue='web')
def analytics_event(
        event_category, event_action, event_label=None, event_value=None,
        **kwargs
):
    """
    Send an analytics event to Google Analytics.

    :see: https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide#event
    :param event_category: the category of the event
    :param event_action: the action of the event (use action words like "click")
    :param event_label: an optional string to differentiate the event
    :param event_value: an optional numeric value for the event
    :param kwargs: extra event parameters to send to GA
    """
    data = {
        't': 'event',  # GA event - don't change
        'ec': event_category,  # Event category (required)
        'ea': event_action,  # Event action (required)
        'el': event_label,  # Event label
        'ev': event_value,  # Event value (numeric)
    }
    data.update(DEFAULT_PARAMETERS)
    data.update(kwargs)
    send_to_analytics(data)
