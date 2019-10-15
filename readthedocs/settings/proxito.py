"""
Local setting for Proxito

These settings will eventually be backported into the main settings file,
but currently we have them to be able to run the site with the old middleware for
a staged rollout of the proxito code.
"""

# pylint: disable=missing-docstring

import os

from readthedocs.settings import base


class ProxitoDevSettings(base.CommunityBaseSettings):

    ROOT_URLCONF = 'readthedocs.proxito.urls'
    USE_SUBDOMAIN = True
    PUBLIC_DOMAIN = 'dev.readthedocs.io'
    PUBLIC_DOMAIN_USES_HTTPS = False

    @property
    def MIDDLEWARE(self):  # noqa
        # Use our new middleware instead of the old one
        classes = super().MIDDLEWARE
        classes = list(classes)
        index = classes.index(
            'readthedocs.core.middleware.SubdomainMiddleware'
        )
        classes[index] = 'readthedocs.proxito.middleware.ProxitoMiddleware'
        classes.remove('readthedocs.core.middleware.SingleVersionMiddleware')
        return classes


ProxitoDevSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        # pylint: disable=unused-wildcard-import
        from .local_settings import *  # noqa
    except ImportError:
        pass
