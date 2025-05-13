"""
Core views.

Including the main homepage, documentation and header rendering,
and server errors.
"""

import structlog
from django.conf import settings
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic import View

from readthedocs.core.forms import SupportForm
from readthedocs.core.mixins import CDNCacheControlMixin
from readthedocs.core.mixins import PrivateViewMixin


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


class HomepageView(View):
    """Conditionally redirect to dashboard or login page."""

    def get(self, request, *args, **kwargs):
        # Redirect to user dashboard for logged in users
        if request.user.is_authenticated:
            return redirect(reverse("projects_dashboard"))

        # Redirect to login page if unauthed
        return redirect(reverse("account_login"))


class WelcomeView(View):
    """
    Conditionally redirect to website home page or to dashboard.

    User hitting readthedocs.org / readthedocs.com is redirected to this view (at /welcome).
    This view will redirect the user based on auth/unauthed:

      1. when user is logged in, redirect to dashboard
      2. when user is logged off, redirect to https://about.readthedocs.com/

    User hitting app.readthedocs.org / app.readthedocs.com
      1. when user is logged in, redirect to dashboard
      2. when user is logged off, redirect to login page
    """

    def get(self, request, *args, **kwargs):
        # Redirect to user dashboard for logged in users
        if request.user.is_authenticated:
            return redirect(reverse("projects_dashboard"))

        # Redirect to ``about.`` in production
        query_string = f"?ref={settings.PRODUCTION_DOMAIN}"
        if request.META["QUERY_STRING"]:
            # Small hack to not append `&` to URLs without a query_string
            query_string += "&" + request.META["QUERY_STRING"]

        # Do a 302 here so that it varies on logged in status
        return redirect(f"https://about.readthedocs.com/{query_string}", permanent=False)


class SupportView(PrivateViewMixin, TemplateView):
    form_class = SupportForm
    template_name = "support/index.html"

    def get_context_data(self, **kwargs):
        """Pass along endpoint for support form."""
        context = super().get_context_data(**kwargs)
        context["SUPPORT_FORM_ENDPOINT"] = settings.SUPPORT_FORM_ENDPOINT
        context["form"] = self.form_class(self.request.user)
        return context


class ErrorView(TemplateView):
    """
    Render templated error pages.

    This can be used both for testing and as a generic error view. This supports
    multiple subpaths for errors, as we need to show application themed errors
    for dashboard users and minimal error pages for documentation readers.

    Template resolution also uses fallback to generic 4xx/5xx error templates.

    View arguments:

    status_code
        This can also be a kwarg, like in the case of a testing view for all
        errors. Set through ``as_view(status_code=504)``, this view will always
        render the same template and status code.

    base_path
        Base path for templates. Dashboard templates can be loaded from a
        separate path from Proxito error templates.
    """

    base_path = "errors/dashboard"
    status_code = None
    template_name = None

    def get_status_code(self):
        return self.kwargs.get("status_code", self.status_code)

    def get_template_name(self):
        return self.kwargs.get("template_name", self.template_name)

    def get_template_names(self):
        template_names = []
        if (template_name := self.get_template_name()) is not None:
            template_names.append(template_name.rstrip("/"))
        if (status_code := self.get_status_code()) is not None:
            template_names.append(str(status_code))
        return [f"{self.base_path}/{file}.html" for file in template_names]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["status_code"] = self.get_status_code()
        return context_data

    def dispatch(self, request, *args, **kwargs):
        context = self.get_context_data()
        status_code = self.get_status_code()
        return self.render_to_response(
            context,
            status=status_code,
        )


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
