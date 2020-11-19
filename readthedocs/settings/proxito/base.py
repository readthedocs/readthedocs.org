"""
Base settings for Proxito

Some of these settings will eventually be backported into the main settings file,
but currently we have them to be able to run the site with the old middleware for
a staged rollout of the proxito code.
"""


class CommunityProxitoSettingsMixin:

    ROOT_URLCONF = 'readthedocs.proxito.urls'
    USE_SUBDOMAIN = True
    SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

    @property
    def DATABASES(self):
        # This keeps connections to the DB alive,
        # which reduces latency with connecting to postgres
        dbs = getattr(super(), 'DATABASES', {})
        for db in dbs:
            dbs[db]['CONN_MAX_AGE'] = 86400
        return dbs

    @property
    def MIDDLEWARE(self):  # noqa
        # Use our new middleware instead of the old one
        classes = super().MIDDLEWARE
        classes = list(classes)
        classes.append('readthedocs.proxito.middleware.ProxitoMiddleware')

        middleware_to_remove = (
            'csp.middleware.CSPMiddleware',
        )
        for mw in middleware_to_remove:
            if mw in classes:
                classes.remove(mw)

        return classes
