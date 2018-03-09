# pylint: disable=missing-docstring
from __future__ import absolute_import

from functools import reduce
from operator import add

from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView
from tastypie.api import Api

from readthedocs.api.base import (ProjectResource, UserResource,
                                  VersionResource, FileResource)
from readthedocs.core.urls import docs_urls, core_urls, deprecated_urls
from readthedocs.core.views import (HomepageView, SupportView,
                                    server_error_404, server_error_500)
from readthedocs.search import views as search_views


v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(ProjectResource())
v1_api.register(VersionResource())
v1_api.register(FileResource())

admin.autodiscover()

handler404 = server_error_404
handler500 = server_error_500

basic_urls = [
    url(r'^$', HomepageView.as_view(), name='homepage'),
    url(r'^support/', SupportView.as_view(), name='support'),
    url(r'^security/', TemplateView.as_view(template_name='security.html')),
    url(r'^.well-known/security.txt',
        TemplateView.as_view(template_name='security.txt', content_type='text/plain')),
]

rtd_urls = [
    url(r'^bookmarks/', include('readthedocs.bookmarks.urls')),
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
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/v2/', include('readthedocs.restapi.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^websupport/', include('readthedocs.comments.urls')),
]

i18n_urls = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

admin_urls = [
    url(r'^admin/', include(admin.site.urls)),
]

debug_urls = add(
    [
        url('style-catalog/$',
            TemplateView.as_view(template_name='style_catalog.html')),
    ],
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

# Export URLs
groups = [basic_urls, rtd_urls, project_urls, api_urls, core_urls, i18n_urls,
          deprecated_urls]

if settings.USE_PROMOS:
    # Include donation URL's
    groups.append([
        url(r'^sustainability/', include('readthedocsext.donate.urls')),
    ])

if 'readthedocsext.embed' in settings.INSTALLED_APPS:
    api_urls.insert(
        0,
        url(r'^api/v1/embed/', include('readthedocsext.embed.urls'))
    )

if not getattr(settings, 'USE_SUBDOMAIN', False) or settings.DEBUG:
    groups.insert(0, docs_urls)
if getattr(settings, 'ALLOW_ADMIN', True):
    groups.append(admin_urls)
if getattr(settings, 'DEBUG', False):
    groups.append(debug_urls)

urlpatterns = reduce(add, groups)
