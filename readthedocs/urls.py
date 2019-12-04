# pylint: disable=missing-docstring
import os
from functools import reduce
from operator import add

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from readthedocs.core.urls import core_urls, docs_urls
from readthedocs.core.views import (
    HomepageView,
    SupportView,
    do_not_track,
    server_error_404,
    server_error_500,
)
from readthedocs.search import views as search_views
from readthedocs.search.api import PageSearchAPIView


admin.autodiscover()

handler404 = server_error_404
handler500 = server_error_500

basic_urls = [
    url(r'^$', HomepageView.as_view(), name='homepage'),
    url(r'^support/', SupportView.as_view(), name='support'),
    url(r'^security/', TemplateView.as_view(template_name='security.html')),
    url(
        r'^\.well-known/security.txt$',
        TemplateView
        .as_view(template_name='security.txt', content_type='text/plain'),
    ),
]

rtd_urls = [
    url(r'^search/$', search_views.elastic_search, name='search'),
    url(r'^dashboard/', include('readthedocs.projects.urls.private')),
    url(r'^profiles/', include('readthedocs.profiles.urls.public')),
    url(r'^accounts/', include('readthedocs.profiles.urls.private')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^notifications/', include('readthedocs.notifications.urls')),
    url(r'^accounts/gold/', include('readthedocs.gold.urls')),
    # For redirects
    url(r'^builds/', include('readthedocs.builds.urls')),
    # For testing the 404's with DEBUG on.
    url(r'^404/$', handler404),
    # For testing the 500's with DEBUG on.
    url(r'^500/$', handler500),
]

project_urls = [
    url(r'^projects/', include('readthedocs.projects.urls.public')),
]

api_urls = [
    url(r'^api/v2/', include('readthedocs.api.v2.urls')),
    # Keep the `doc_search` at root level, so the test does not fail for other API
    url(r'^api/v2/docsearch/$', PageSearchAPIView.as_view(), name='doc_search'),
    url(
        r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    url(r'^api/v3/', include('readthedocs.api.v3.urls')),
]

i18n_urls = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

admin_urls = [
    url(r'^admin/', admin.site.urls),
]

dnt_urls = [
    url(r'^\.well-known/dnt/$', do_not_track),

    # https://github.com/EFForg/dnt-guide#12-how-to-assert-dnt-compliance
    url(
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
    url(
        'style-catalog/$',
        TemplateView.as_view(template_name='style_catalog.html'),
    ),

    # This must come last after the build output files
    url(
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
    api_urls,
    core_urls,
    i18n_urls,
]

if settings.DO_NOT_TRACK_ENABLED:
    # Include Do Not Track URLs if DNT is supported
    groups.append(dnt_urls)


if settings.READ_THE_DOCS_EXTENSIONS:
    groups.append([
        url(r'^', include('readthedocsext.urls'))
    ])

if not settings.USE_SUBDOMAIN or settings.DEBUG:
    groups.insert(0, docs_urls)
if settings.ALLOW_ADMIN:
    groups.append(admin_urls)
if settings.DEBUG:
    import debug_toolbar

    debug_urls += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    groups.append(debug_urls)

urlpatterns = reduce(add, groups)
