"""Template context processors for core app."""

from __future__ import absolute_import
from django.conf import settings


def readthedocs_processor(request):
    # pylint: disable=unused-argument
    exports = {
        'PUBLIC_DOMAIN': getattr(settings, 'PUBLIC_DOMAIN', None),
        'PRODUCTION_DOMAIN': getattr(settings, 'PRODUCTION_DOMAIN', None),
        'USE_SUBDOMAINS': getattr(settings, 'USE_SUBDOMAINS', None),
        'GLOBAL_ANALYTICS_CODE': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
        'SITE_ROOT': getattr(settings, 'SITE_ROOT', '') + '/',
        'TEMPLATE_ROOT': getattr(settings, 'TEMPLATE_ROOT', '') + '/',
    }
    return exports
