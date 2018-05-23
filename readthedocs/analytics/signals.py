"""Django signal receivers for the analytics app."""

from __future__ import absolute_import, unicode_literals
import logging

from django.dispatch import receiver

from readthedocs.restapi.signals import footer_response

from .tasks import analytics_event
from .utils import get_client_ip


log = logging.getLogger(__name__)   # noqa


@receiver(footer_response)
def fire_analytics_event(sender, **kwargs):
    """Fires a server side google analytics event when the footer API is called"""
    del sender  # unused
    request = kwargs['request']
    context = kwargs['context']
    project = context['project']

    data = {
        'ec': 'footer-api',
        'ea': 'load',
        'el': project.slug,

        # User data
        'ua': request.META.get('HTTP_USER_AGENT'),
        'uip': get_client_ip(request),
    }

    analytics_event.delay(data)

    log.info('Fired analytics event for project "{}"'.format(project))
    log.info(' - Path: {}'.format(request.build_absolute_uri()))
