"""
Base settings for Proxito

Some of these settings will eventually be backported into the main settings file,
but currently we have them to be able to run the site with the old middleware for
a staged rollout of the proxito code.
"""
import structlog

log = structlog.get_logger(__name__)


class CommunityProxitoSettingsMixin:
    ROOT_URLCONF = "readthedocs.proxito.urls"
    SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

    # Allow cookies from cross-site requests on subdomains for now.
    # As 'Lax' breaks when the page is embedded in an iframe.
    SESSION_COOKIE_SAMESITE = "None"

    @property
    def DATABASES(self):
        # This keeps connections to the DB alive,
        # which reduces latency with connecting to postgres
        dbs = getattr(super(), "DATABASES", {})
        for db in dbs:
            dbs[db]["CONN_MAX_AGE"] = 86400
        return dbs

    @property
    def MIDDLEWARE(self):  # noqa
        # Use our new middleware instead of the old one
        classes = super().MIDDLEWARE
        classes = list(classes)
        classes.append("readthedocs.proxito.middleware.ProxitoMiddleware")

        middleware_to_remove = (
            # We don't need or want to allow cross site requests in proxito.
            "corsheaders.middleware.CorsMiddleware",
            "csp.middleware.CSPMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        )
        for mw in middleware_to_remove:
            if mw in classes:
                classes.remove(mw)
            else:
                log.warning("Failed to remove middleware.", middleware=mw)

        return classes
