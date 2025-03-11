import structlog
from django.http import HttpResponse
from django.shortcuts import render

from readthedocs.core.views import ErrorView

from ..exceptions import ContextualizedHttp404


log = structlog.get_logger(__name__)  # noqa


class ProxitoErrorView(ErrorView):
    base_path = "errors/proxito"


def fast_404(request, *args, **kwargs):
    """
    A fast error page handler.

    This stops us from running RTD logic in our error handling. We already do
    this in RTD prod when we fallback to it.
    """
    return HttpResponse("Not Found.", status=404)


def proxito_404_page_handler(request, template_name="errors/proxito/404/base.html", exception=None):
    """
    Serves a 404 error message, handling 404 exception types raised throughout the app.

    We want to return fast when the 404 is used as an internal NGINX redirect to
    reach our ``ServeError404`` view. However, if the 404 exception was risen
    inside ``ServeError404`` view, we want to render a useful HTML response.
    """

    # 404 exceptions that don't originate from our proxito 404 handler should have a fast response
    # with no HTML rendered, since they will be forwarded to our 404 handler again.
    if request.resolver_match and request.resolver_match.url_name != "proxito_404_handler":
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
