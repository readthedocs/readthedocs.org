"""Template context processors for core app."""

from django.conf import settings


def readthedocs_processor(request):
    exports = {
        "PUBLIC_DOMAIN": settings.PUBLIC_DOMAIN,
        "PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
        "USE_SUBDOMAIN": settings.USE_SUBDOMAIN,
        "GLOBAL_ANALYTICS_CODE": settings.GLOBAL_ANALYTICS_CODE,
        "DASHBOARD_ANALYTICS_CODE": settings.DASHBOARD_ANALYTICS_CODE,
        "SITE_ROOT": settings.SITE_ROOT + "/",
        "TEMPLATE_ROOT": settings.TEMPLATE_ROOT + "/",
        "DO_NOT_TRACK_ENABLED": settings.DO_NOT_TRACK_ENABLED,
        "USE_PROMOS": settings.USE_PROMOS,
        "USE_ORGANIZATIONS": settings.RTD_ALLOW_ORGANIZATIONS,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
    }
    return exports
