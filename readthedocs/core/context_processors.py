"""Template context processors for core app."""

from django.conf import settings


def readthedocs_processor(request):
    """
    Context processor to include global settings to templates.

    Note that we are not using the ``request`` object at all here.
    It's preferable to keep it like that since it's used from places where there is no request.

    If you need to add something that depends on the request,
    create a new context processor.
    """

    exports = {
        "PUBLIC_DOMAIN": settings.PUBLIC_DOMAIN,
        "PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
        "GLOBAL_ANALYTICS_CODE": settings.GLOBAL_ANALYTICS_CODE,
        "DASHBOARD_ANALYTICS_CODE": settings.DASHBOARD_ANALYTICS_CODE,
        "SITE_ROOT": settings.SITE_ROOT + "/",
        "TEMPLATE_ROOT": settings.TEMPLATE_ROOT + "/",
        "DO_NOT_TRACK_ENABLED": settings.DO_NOT_TRACK_ENABLED,
        "USE_PROMOS": settings.USE_PROMOS,
        "USE_ORGANIZATIONS": settings.RTD_ALLOW_ORGANIZATIONS,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "PUBLIC_API_URL": settings.PUBLIC_API_URL,
        "ADMIN_URL": settings.ADMIN_URL,
        "GITHUB_APP_NAME": settings.GITHUB_APP_NAME,
    }
    return exports


def user_notifications(request):
    """
    Context processor to include user's notification to templates.

    We can't use ``request.user.notifications.all()`` because we are not using a ``CustomUser``.
    If we want to go that route, we should define a ``CustomUser`` and define a ``GenericRelation``.

    See https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-AUTH_USER_MODEL
    """

    # Import here due to circular import
    from readthedocs.notifications.models import Notification

    user_notifications = Notification.objects.none()
    if request.user.is_authenticated:
        user_notifications = Notification.objects.for_user(
            request.user,
            resource=request.user,
        )

    return {
        "user_notifications": user_notifications,
    }
