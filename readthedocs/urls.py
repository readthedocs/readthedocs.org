import os
from functools import reduce
from operator import add

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from impersonate.views import impersonate
from impersonate.views import stop_impersonate

from readthedocs.core.views import ErrorView
from readthedocs.core.views import HomepageView
from readthedocs.core.views import SupportView
from readthedocs.core.views import WelcomeView
from readthedocs.core.views import do_not_track
from readthedocs.search.views import GlobalSearchView


admin.autodiscover()

handler400 = ErrorView.as_view(status_code=400)
handler403 = ErrorView.as_view(status_code=403)
handler404 = ErrorView.as_view(status_code=404)
handler500 = ErrorView.as_view(status_code=500)
# Rate limit handler for allauth views,
# this isn't a Django built-in handler.
# https://docs.allauth.org/en/latest/account/rate_limits.html.
handler429 = ErrorView.as_view(status_code=429)

basic_urls = [
    path("", HomepageView.as_view(), name="homepage"),
    path("welcome/", WelcomeView.as_view(), name="welcome"),
    path(
        "security/",
        RedirectView.as_view(url="https://docs.readthedocs.com/platform/stable/security.html"),
    ),
    re_path(
        r"^\.well-known/security.txt$",
        TemplateView.as_view(template_name="security.txt", content_type="text/plain"),
    ),
    path("support/", SupportView.as_view(), name="support"),
    # These are redirected to from the support form
    path(
        "support/success/",
        TemplateView.as_view(template_name="support/success.html"),
        name="support_success",
    ),
    path(
        "support/error/",
        TemplateView.as_view(template_name="support/error.html"),
        name="support_error",
    ),
]

rtd_urls = [
    path("search/", GlobalSearchView.as_view(), name="search"),
    path("dashboard/", include("readthedocs.projects.urls.private")),
    path("profiles/", include("readthedocs.profiles.urls.public")),
    path("accounts/", include("readthedocs.profiles.urls.private")),
    path("accounts/", include("allauth.urls")),
    path("accounts/gold/", include("readthedocs.gold.urls")),
    path("invitations/", include("readthedocs.invitations.urls")),
    # For redirects
    path("builds/", include("readthedocs.builds.urls")),
    # Put this as a unique path for the webhook, so we don't clobber existing Stripe URL's
    path("djstripe/", include("djstripe.urls", namespace="djstripe")),
    path("webhook/", include("readthedocs.oauth.urls")),
]

project_urls = [
    path("projects/", include("readthedocs.projects.urls.public")),
]


organization_urls = [
    path(
        "organizations/",
        include("readthedocs.organizations.urls.private"),
    ),
    path(
        "organizations/",
        include("readthedocs.organizations.urls.public"),
    ),
    re_path(
        r"^organizations/(?P<slug>[\w.-]+)/subscription/",
        include("readthedocs.subscriptions.urls"),
    ),
    path(
        "pricing/",
        RedirectView.as_view(url="https://about.readthedocs.com/pricing/#/community"),
        name="pricing",
    ),
]


api_urls = [
    path("api/v2/", include("readthedocs.api.v2.urls")),
    # Keep `search_api` at root level, so the test does not fail for other API
    path("api/v2/search/", include("readthedocs.search.api.v2.urls")),
    path("api/v3/search/", include("readthedocs.search.api.v3.urls")),
    # Deprecated
    path("api/v1/embed/", include("readthedocs.embed.urls")),
    path("api/v2/embed/", include("readthedocs.embed.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/v3/", include("readthedocs.api.v3.urls")),
    path("api/v3/embed/", include("readthedocs.embed.v3.urls")),
]

i18n_urls = [
    path("i18n/", include("django.conf.urls.i18n")),
]

admin_urls = [
    re_path(r"^admin/", admin.site.urls),
]

impersonate_urls = [
    # We don't use ``include('impersonate.urls')`` here because we don't want to
    # define ``/search`` and ``/list`` URLs
    path(
        "impersonate/stop/",
        stop_impersonate,
        name="impersonate-stop",
    ),
    path(
        "impersonate/<path:uid>/",
        impersonate,
        name="impersonate-start",
    ),
]


dnt_urls = [
    re_path(r"^\.well-known/dnt/$", do_not_track),
    # https://github.com/EFForg/dnt-guide#12-how-to-assert-dnt-compliance
    re_path(
        r"^\.well-known/dnt-policy.txt$",
        TemplateView.as_view(template_name="dnt-policy.txt", content_type="text/plain"),
    ),
]

debug_urls = []
for build_format in ("epub", "htmlzip", "json", "pdf"):
    debug_urls += static(
        settings.MEDIA_URL + build_format,
        document_root=os.path.join(settings.MEDIA_ROOT, build_format),
    )
debug_urls += [
    path(
        "style-catalog/",
        TemplateView.as_view(template_name="style_catalog.html"),
    ),
    # For testing error responses and templates
    re_path(
        r"^error/(?P<template_name>.*)$",
        ErrorView.as_view(),
    ),
    # This must come last after the build output files
    path(
        "media/<path:remainder>",
        RedirectView.as_view(url=settings.STATIC_URL + "%(remainder)s"),
        name="media-redirect",
    ),
]

# Export URLs
groups = [
    basic_urls,
    rtd_urls,
    project_urls,
    organization_urls,
    api_urls,
    i18n_urls,
]

if settings.DO_NOT_TRACK_ENABLED:
    # Include Do Not Track URLs if DNT is supported
    groups.append(dnt_urls)


if settings.READ_THE_DOCS_EXTENSIONS:
    groups.append([path("", include("readthedocsext.urls"))])

if settings.ALLOW_ADMIN:
    groups.append(admin_urls)
    groups.append(impersonate_urls)

if settings.SHOW_DEBUG_TOOLBAR:
    import debug_toolbar

    debug_urls += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    groups.append(debug_urls)

urlpatterns = reduce(add, groups)
