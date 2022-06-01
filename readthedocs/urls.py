# pylint: disable=missing-docstring
import os
from functools import reduce
from operator import add

from django.conf import settings
from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from readthedocs.core.views import (
    HomepageView,
    SupportView,
    do_not_track,
    server_error_500,
)
from readthedocs.search.api import PageSearchAPIView
from readthedocs.search.views import GlobalSearchView

admin.autodiscover()

handler500 = server_error_500

basic_urls = [
    re_path(r'^$', HomepageView.as_view(), name='homepage'),
    re_path(r'^security/', TemplateView.as_view(template_name='security.html')),
    re_path(
        r'^\.well-known/security.txt$',
        TemplateView
        .as_view(template_name='security.txt', content_type='text/plain'),
    ),
    re_path(r'^support/$', SupportView.as_view(), name='support'),
    # These are redirected to from the support form
    re_path(
        r'^support/success/$',
        TemplateView.as_view(template_name='support/success.html'),
        name='support_success',
    ),
    re_path(
        r'^support/error/$',
        TemplateView.as_view(template_name='support/error.html'),
        name='support_error',
    ),
]

rtd_urls = [
    re_path(r'^search/$', GlobalSearchView.as_view(), name='search'),
    re_path(r'^dashboard/', include('readthedocs.projects.urls.private')),
    re_path(r'^profiles/', include('readthedocs.profiles.urls.public')),
    re_path(r'^accounts/', include('readthedocs.profiles.urls.private')),
    re_path(r'^accounts/', include('allauth.urls')),
    re_path(r'^notifications/', include('readthedocs.notifications.urls')),
    re_path(r'^accounts/gold/', include('readthedocs.gold.urls')),
    # For redirects
    re_path(r'^builds/', include('readthedocs.builds.urls')),
    # For testing the 500's with DEBUG on.
    re_path(r'^500/$', handler500),
    # Put this as a unique path for the webhook, so we don't clobber existing Stripe URL's
    # re_path(r"^djstripe/", include("djstripe.urls", namespace="djstripe")),
]

project_urls = [
    re_path(r'^projects/', include('readthedocs.projects.urls.public')),
]


organization_urls = [
    re_path(
        r'^organizations/',
        include('readthedocs.organizations.urls.private'),
    ),
    re_path(
        r'^organizations/',
        include('readthedocs.organizations.urls.public'),
    ),
    re_path(
        r'^organizations/(?P<slug>[\w.-]+)/subscription/',
        include('readthedocs.subscriptions.urls'),
    ),
    # NOTE: This is overridden in .com to serve a real pricing page.
    re_path(
        r'^pricing/',
        RedirectView.as_view(url='https://readthedocs.org/sustainability/'),
        name='pricing',
    ),
]


api_urls = [
    re_path(r'^api/v2/', include('readthedocs.api.v2.urls')),
    # Keep `search_api` at root level, so the test does not fail for other API
    re_path(r'^api/v2/search/$', PageSearchAPIView.as_view(), name='search_api'),
    # Deprecated
    re_path(r'^api/v1/embed/', include('readthedocs.embed.urls')),
    re_path(r'^api/v2/embed/', include('readthedocs.embed.urls')),
    re_path(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    re_path(r'^api/v3/', include('readthedocs.api.v3.urls')),
    re_path(r'^api/v3/embed/', include('readthedocs.embed.v3.urls')),
]

i18n_urls = [
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
]

admin_urls = [
    re_path(r'^admin/', admin.site.urls),
]

dnt_urls = [
    re_path(r'^\.well-known/dnt/$', do_not_track),

    # https://github.com/EFForg/dnt-guide#12-how-to-assert-dnt-compliance
    re_path(
        r'^\.well-known/dnt-policy.txt$',
        TemplateView
        .as_view(template_name='dnt-policy.txt', content_type='text/plain'),
    ),
]

debug_urls = []
for build_format in ('epub', 'htmlzip', 'json', 'pdf'):
    debug_urls += static(
        settings.MEDIA_URL + build_format,
        document_root=os.path.join(settings.MEDIA_ROOT, build_format),
    )
debug_urls += [
    re_path(
        'style-catalog/$',
        TemplateView.as_view(template_name='style_catalog.html'),
    ),

    # This must come last after the build output files
    re_path(
        r'^media/(?P<remainder>.+)$',
        RedirectView.as_view(url=settings.STATIC_URL + '%(remainder)s'),
        name='media-redirect',
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
    groups.append([
        re_path(r'^', include('readthedocsext.urls'))
    ])

if settings.ALLOW_ADMIN:
    groups.append(admin_urls)

if settings.DEBUG:
    import debug_toolbar

    debug_urls += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    groups.append(debug_urls)

urlpatterns = reduce(add, groups)
