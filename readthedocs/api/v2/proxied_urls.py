"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf import settings
from django.conf.urls import include, url

from readthedocs.analytics.proxied_api import AnalyticsView
from readthedocs.search.proxied_api import ProxiedPageSearchAPIView

from .views.proxied import ProxiedFooterHTML

api_footer_urls = [
    url(r'footer_html/', ProxiedFooterHTML.as_view(), name='footer_html'),
    url(r'search/$', ProxiedPageSearchAPIView.as_view(), name='search_api'),
    url(r'embed/', include('readthedocs.embed.urls')),
    url(r'analytics/$', AnalyticsView.as_view(), name='analytics_api'),
]

urlpatterns = api_footer_urls
