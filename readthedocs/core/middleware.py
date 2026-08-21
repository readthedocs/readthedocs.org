from urllib.parse import urlparse

import structlog
from django.conf import settings
from django.core.exceptions import TooManyFieldsSent
from django.http import HttpResponse
from django.utils import timezone


log = structlog.get_logger(__name__)


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
        try:
            query_params = request.GET.items()
        except TooManyFieldsSent:
            log.info(
                "Too many GET parameters in request.",
                url=request.build_absolute_uri(),
            )
            return HttpResponse(
                "The number of GET parameters exceeded the maximum allowed.",
                status=400,
            )

        for key, value in query_params:
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


class FirstTouchAttributionMiddleware:
    """
    Capture first-touch marketing attribution for anonymous visitors.

    On the first request of a session that carries an attribution signal
    (any ``utm_*`` query parameter, a ``ref`` query parameter, or an external
    referrer), store the signal in the session. If the visitor later signs up,
    the ``user_signed_up`` receiver copies it onto their profile
    (see :py:func:`readthedocs.core.signals.store_first_touch_attribution`).

    First touch wins: once captured, the session data is never overwritten.
    Nothing is stored for visitors without a signal, so plain direct traffic
    doesn't create sessions.
    """

    SESSION_KEY = "attribution"
    UTM_PARAMS = [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
    ]
    MAX_LENGTH = 512

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            self._capture(request)
        except Exception:
            # Attribution is best effort, never break the request over it.
            log.exception("Error capturing first-touch attribution.")
        return self.get_response(request)

    def _capture(self, request):
        if request.method != "GET" or request.user.is_authenticated:
            return

        # Skip requests that aren't browser navigation (API calls from docs
        # pages carry a Referer header, and their clients don't send cookies,
        # so capturing there would create one session per request).
        if request.path.startswith("/api/"):
            return

        if self.SESSION_KEY in request.session:
            return

        data = {}
        for param in self.UTM_PARAMS:
            value = request.GET.get(param, "").strip()
            if value:
                data[param] = value[: self.MAX_LENGTH]

        referrer = self._get_external_referrer(request)
        if referrer:
            data["referrer"] = referrer[: self.MAX_LENGTH]

        # Only store when there is an actual signal.
        if not data:
            return

        data["landing_page"] = request.path[: self.MAX_LENGTH]
        data["first_touch_date"] = timezone.now().isoformat()
        request.session[self.SESSION_KEY] = data

    def _get_external_referrer(self, request):
        """
        Get the referrer of the request, only if it's external.

        The ``ref`` query parameter takes precedence over the ``Referer``
        header, since our websites use it to forward the original referrer
        across domains (about.readthedocs.com can't share cookies with the
        dashboard).
        """
        ref = request.GET.get("ref", "").strip()
        if ref:
            return ref

        referrer = request.headers.get("Referer", "").strip()
        if not referrer:
            return None

        # Ignore internal navigation, only the traffic source is interesting.
        try:
            referrer_host = urlparse(referrer).netloc
        except ValueError:
            return None
        if not referrer_host or referrer_host == request.get_host():
            return None

        return referrer


class UpdateCSPMiddleware:
    """
    Middleware to update the CSP headers for specific views given its URL name.

    This is useful for views that we don't have much control over,
    like views from third-party packages. For views that we have control over,
    we should update the CSP headers directly in the view.

    Use the `RTD_CSP_UPDATE_HEADERS` setting to define the views that need to
    update the CSP headers. The setting should be a dictionary where the key is
    the URL name of the view and the value is a dictionary with the CSP headers,
    for example:

    .. code-block:: python

       RTD_CSP_UPDATE_HEADERS = {
           "login": {"form-action": ["https:"]},
       }
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Views that raised an exception don't have a resolver_match object.
        resolver_match = request.resolver_match
        if not resolver_match:
            return response

        url_name = resolver_match.url_name
        update_csp_headers = settings.RTD_CSP_UPDATE_HEADERS
        if url_name in update_csp_headers:
            if hasattr(response, "_csp_update"):
                raise ValueError(
                    "Can't update CSP headers at the view and middleware at the same time, use one or the other."
                )
            response._csp_update = update_csp_headers[url_name]

        return response
