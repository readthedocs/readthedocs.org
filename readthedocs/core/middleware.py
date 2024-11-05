import structlog
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
