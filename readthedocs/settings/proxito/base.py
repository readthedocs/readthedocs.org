"""
Base settings for Proxito

Some of these settings will eventually be backported into the main settings file,
but currently we have them to be able to run the site with the old middleware for
a staged rollout of the proxito code.
"""

class CommunityProxitoSettingsMixin:

    ROOT_URLCONF = 'readthedocs.proxito.urls'
    USE_SUBDOMAIN = True

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
        return tuple(classes)
