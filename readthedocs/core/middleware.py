import structlog
from django.conf import settings
from django.core.exceptions import TooManyFieldsSent
from django.http import HttpResponse


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


class AttributionMiddleware:
    """
    Stash signup attribution from the URL into the session.

    Our marketing site adds these parameters to its signup links, carrying
    over where the visitor originally came from. We keep them in the session
    so they survive the trip through an OAuth provider, and store them on the
    user at signup (see
    :py:func:`readthedocs.core.signals.store_signup_attribution`).

    First touch wins, and requests without any of these parameters are
    ignored, so normal traffic doesn't create sessions.
    """

    SESSION_KEY = "attribution"
    # Keep in sync with the parameters our website adds to signup links,
    # see ``src/js/attribution.js`` in the website repository.
    PARAMS = ["utm_source", "utm_medium", "utm_campaign", "ref"]
    MAX_LENGTH = 255

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET":
            data = {
                param: request.GET[param].strip()[: self.MAX_LENGTH]
                for param in self.PARAMS
                if request.GET.get(param, "").strip()
            }
            # Checked in this order so that requests without these parameters
            # -- almost all of them -- don't load the session at all.
            if (
                data
                and not request.user.is_authenticated
                and self.SESSION_KEY not in request.session
            ):
                request.session[self.SESSION_KEY] = data

        return self.get_response(request)


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
