"""Integration utility functions"""


def normalize_request_payload(request):
    """Normalize the request body, hopefully to JSON

    This will attempt to return a JSON body, backing down to a string body next.

    :param request: HTTP request object
    :type request: django.http.HttpRequest
    :returns: The request body as a string
    :rtype: str
    """
    request_payload = getattr(request, 'data', {})
    if request.content_type != 'application/json':
        # Here, request_body can be a dict or a MergeDict. Probably best to
        # normalize everything first
        try:
            request_payload = dict(list(request_payload.items()))
        except AttributeError:
            pass
    return request_payload
