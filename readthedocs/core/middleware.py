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

    Our marketing site adds a ``ref`` parameter to its signup links, carrying
    over where the visitor originally came from. We keep it in the session so
    it survives the trip through an OAuth provider, and store it on the user
    at signup (see
    :py:func:`readthedocs.core.signals.store_signup_attribution`).

    The value is a slash separated source, medium and campaign, with only the
    source required, so ``?ref=hn`` and ``?ref=newsletter/email/launch`` are
    both valid. We use one parameter instead of the usual ``utm_*`` set
    because those are for our website's analytics, which has already resolved
    them into a single answer by the time it links here. This matches the
    ``?ref=`` that :py:class:`readthedocs.core.views.WelcomeView` already adds
    when it sends visitors from our old domains to the website.

    First touch wins, and requests without a ``ref`` are ignored, so normal
    traffic doesn't create sessions.
    """

    SESSION_KEY = "attribution"
    # Keep in sync with the value our website builds,
    # see ``src/js/attribution.js`` in the website repository.
    PARAM = "ref"
    KEYS = ["source", "medium", "campaign"]
    MAX_LENGTH = 100

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET":
            data = self.parse(request.GET.get(self.PARAM, ""))
            # Checked in this order so that requests without a ``ref`` --
            # almost all of them -- don't load the session at all.
            if (
                data
                and not request.user.is_authenticated
                and self.SESSION_KEY not in request.session
            ):
                request.session[self.SESSION_KEY] = data

        return self.get_response(request)

    @classmethod
    def parse(cls, ref):
        """Parse a ``ref`` value into its named parts, ignoring empty ones."""
        parts = ref.strip().split("/", len(cls.KEYS) - 1)
        return {
            key: part.strip()[: cls.MAX_LENGTH]
            for key, part in zip(cls.KEYS, parts)
            if part.strip()
        }


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
