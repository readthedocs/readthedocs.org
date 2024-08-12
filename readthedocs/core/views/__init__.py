"""
Core views.

Including the main homepage, documentation and header rendering,
and server errors.
"""

import structlog
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from readthedocs.core.forms import SupportForm
from readthedocs.core.mixins import CDNCacheControlMixin, PrivateViewMixin

log = structlog.get_logger(__name__)


class NoProjectException(Exception):
    pass


class HealthCheckView(CDNCacheControlMixin, View):
    # Never cache this view, we always want to get the live response from the server.
    # In production we should configure the health check to hit the LB directly,
    # but it's useful to be careful here in case of a misconfiguration.
    cache_response = False

    def get(self, request, *_, **__):
        return JsonResponse({"status": 200}, status=200)


class HomepageView(TemplateView):

    """
    Conditionally show the home page or redirect to the login page.

    On the current dashboard, this shows the application homepage. However, we
    no longer require this page in our application as we have a similar page on
    our website. Instead, redirect to our login page on the new dashboard.
    """

    template_name = "homepage.html"

    def get(self, request, *args, **kwargs):
        # Redirect to login page for new dashboard
        if settings.RTD_EXT_THEME_ENABLED:
            return redirect(reverse("account_login"))

        # Redirect to user dashboard for logged in users
        if request.user.is_authenticated:
            return redirect("projects_dashboard")

        # Redirect to ``about.`` in production
        if not settings.DEBUG:
            query_string = f"?ref={settings.PRODUCTION_DOMAIN}"
            if request.META["QUERY_STRING"]:
                # Small hack to not append `&` to URLs without a query_string
                query_string += "&" + request.META["QUERY_STRING"]

            # Do a 302 here so that it varies on logged in status
            return redirect(
                f"https://about.readthedocs.com{query_string}", permanent=False
            )

        # Show the homepage for local dev
        return super().get(request, *args, **kwargs)


class SupportView(PrivateViewMixin, TemplateView):
    form_class = SupportForm
    template_name = "support/index.html"

    def get_context_data(self, **kwargs):
        """Pass along endpoint for support form."""
        context = super().get_context_data(**kwargs)
        context["SUPPORT_FORM_ENDPOINT"] = settings.SUPPORT_FORM_ENDPOINT

        if settings.RTD_EXT_THEME_ENABLED:
            context["form"] = self.form_class(self.request.user)

        return context


class ErrorView(TemplateView):

    """
    Render templated error pages.

    This can be used both for testing and as a generic error view. This supports
    multiple subpaths for errors, as we need to show application themed errors
    for dashboard users and minimal error pages for documentation readers.

    View arguments:

    status_code
        This can also be a kwarg, like in the case of a testing view for all
        errors. Set through ``as_view(status_code=504)``, this view will always
        render the same template and status code.

    base_path
        Base path for templates. Dashboard templates can be loaded from a
        separate path from Proxito error templates.
    """

    base_path = "errors/dashboard/"
    status_code = 500

    def get_status_code(self):
        status_code = self.status_code
        try:
            status_code = int(self.kwargs["status_code"])
        except (ValueError, KeyError):
            pass
        return status_code

    def get_template_names(self):
        status_code = self.get_status_code()
        if settings.RTD_EXT_THEME_ENABLED:
            # First try to load the template for the specific HTTP status code
            # and fall back to a generic 400/500 level error template
            status_code_class = int(status_code / 100)
            generic_code = f"{status_code_class}xx"
            return [
                f"{self.base_path}/{code}.html" for code in [status_code, generic_code]
            ]
        # TODO the legacy dashboard has top level path errors, as is the
        # default. This can be removed later.
        return f"{status_code}.html"

    def dispatch(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        status_code = self.get_status_code()
        return self.render_to_response(
            context,
            status=status_code,
        )


# TODO replace this with ErrorView and a template in `errors/` instead
class TeapotView(TemplateView):
    template_name = "core/teapot.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=418)


class PageNotFoundView(View):

    """Just a 404 view that ignores all URL parameters."""

    def get(self, request, *args, **kwargs):
        raise Http404()


def do_not_track(request):
    dnt_header = request.headers.get("Dnt")

    # https://w3c.github.io/dnt/drafts/tracking-dnt.html#status-representation
    return JsonResponse(  # pylint: disable=redundant-content-type-for-json-response
        {
            "policy": "https://docs.readthedocs.io/en/latest/privacy-policy.html",
            "same-party": [
                "readthedocs.org",
                "readthedocs.com",
                "readthedocs.io",  # .org Documentation Sites
                "readthedocs-hosted.com",  # .com Documentation Sites
            ],
            "tracking": "N" if dnt_header == "1" else "T",
        },
        content_type="application/tracking-status+json",
    )
