import datetime

import pytz
import structlog
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from ..exceptions import ContextualizedHttp404

log = structlog.get_logger(__name__)  # noqa


def fast_404(request, *args, **kwargs):
    """
    A fast error page handler.

    This stops us from running RTD logic in our error handling. We already do
    this in RTD prod when we fallback to it.
    """
    return HttpResponse("Not Found.", status=404)


def proxito_404_page_handler(
    request, template_name="errors/404/base.html", exception=None
):
    """
    Serves a 404 error message, handling 404 exception types raised throughout the app.

    We want to return fast when the 404 is used as an internal NGINX redirect to
    reach our ``ServeError404`` view. However, if the 404 exception was risen
    inside ``ServeError404`` view, we want to render a useful HTML response.
    """

    # 404 exceptions that don't originate from our proxito 404 handler should have a fast response
    # with no HTML rendered, since they will be forwarded to our 404 handler again.
    if (
        request.resolver_match
        and request.resolver_match.url_name != "proxito_404_handler"
    ):
        return fast_404(request, exception, template_name)

    context = {}
    http_status = 404

    # Contextualized 404 exceptions:
    # Context is defined by the views that raise these exceptions and handled
    # in their templates.
    if isinstance(exception, ContextualizedHttp404):
        context.update(exception.get_context())
        template_name = exception.template_name
        http_status = exception.http_status

    context["path_not_found"] = context.get("path_not_found") or request.path

    r = render(
        request,
        template_name,
        context=context,
    )
    r.status_code = http_status
    return r


def allow_readme_html_at_root_url():
    tzinfo = pytz.timezone("America/Los_Angeles")
    now = datetime.datetime.now(tz=tzinfo)

    # Brownout dates as published in https://about.readthedocs.com/blog/2024/05/readme-html-deprecated/
    # fmt: off
    return not any([
        # 12 hours browndate
        datetime.datetime(2024, 6, 10, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 6, 10, 12, 0, 0, tzinfo=tzinfo),
        # 24 hours browndate
        datetime.datetime(2024, 6, 17, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 6, 18, 0, 0, 0, tzinfo=tzinfo),
        # 48 hours browndate
        datetime.datetime(2024, 6, 24, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2024, 6, 26, 0, 0, 0, tzinfo=tzinfo),
        # Deprecated after July 1st
        datetime.datetime(2024, 7, 1, 0, 0, 0, tzinfo=tzinfo) < now,
    ]) and settings.RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS
    # fmt: on
