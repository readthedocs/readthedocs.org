import structlog
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.http import HttpResponse

log = structlog.get_logger(__name__)


class ReadTheDocsSessionMiddleware(SessionMiddleware):

    """
    An overridden session middleware with a few changes.

    - Doesn't create a session on logged out doc views.
    """

    # Don't set a session cookie on these URLs unless the cookie is already set
    IGNORE_URLS = [
        "/api/v2/footer_html",
        "/sustainability/view",
        "/sustainability/click",
    ]

    def process_request(self, request):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url)
                and settings.SESSION_COOKIE_NAME not in request.COOKIES
            ):
                # Hack request.session otherwise the Authentication middleware complains.
                request.session = SessionBase()  # create an empty session
                return

        super().process_request(request)

    def process_response(self, request, response):
        for url in self.IGNORE_URLS:
            if (
                request.path_info.startswith(url)
                and settings.SESSION_COOKIE_NAME not in request.COOKIES
            ):
                return response

        return super().process_response(request, response)


class ReferrerPolicyMiddleware:

    """
    A middleware implementing the Referrer-Policy header.

    The value of the header will be read from the SECURE_REFERRER_POLICY setting.

    Important:
        In Django 3.x, this feature is built-in to the SecurityMiddleware.
        After upgrading to Django3, this middleware should be removed.
        https://docs.djangoproject.com/en/3.1/ref/middleware/#referrer-policy

    Based heavily on: https://github.com/ubernostrum/django-referrer-policy
    """

    VALID_REFERRER_POLICIES = [
        "no-referrer",
        "no-referrer-when-downgrade",
        "origin",
        "origin-when-cross-origin",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "unsafe-url",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

        if not settings.SECURE_REFERRER_POLICY:
            log.warning(
                "SECURE_REFERRER_POLICY not set - not setting the referrer policy"
            )
            raise MiddlewareNotUsed()
        if settings.SECURE_REFERRER_POLICY not in self.VALID_REFERRER_POLICIES:
            raise ImproperlyConfigured(
                "settings.SECURE_REFERRER_POLICY has an illegal value."
            )

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = settings.SECURE_REFERRER_POLICY
        return response


class NullCharactersMiddleware:

    """
    Block all requests that contains NULL characters (0x00) on their GET attributes.

    Requests containing NULL characters make our code to break. In particular,
    when trying to save the content containing a NULL character into the
    database, producing a 500 and creating an event in Sentry.

    NULL characters are also used as an explotation technique, known as "Null Byte Injection".
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for key, value in request.GET.items():
            if "\x00" in value:
                log.info(
                    "NULL (0x00) characters in GET attributes.",
                    attribute=key,
                    value=value,
                    url=request.build_absolute_uri(),
                )
                return HttpResponse(
                    "There are NULL (0x00) characters in at least one of the parameters passed to the request.",
                    status=400,
                )
        return self.get_response(request)
