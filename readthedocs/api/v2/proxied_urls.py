"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf.urls import re_path

from readthedocs.analytics.proxied_api import AnalyticsView
from readthedocs.api.v2.views.proxied import ProxiedEmbedAPI, ProxiedFooterHTML
from readthedocs.search.proxied_api import ProxiedPageSearchAPIView

api_footer_urls = [
    re_path(r'footer_html/', ProxiedFooterHTML.as_view(), name='footer_html'),
    re_path(r'search/$', ProxiedPageSearchAPIView.as_view(), name='search_api'),
    re_path(r'embed/', ProxiedEmbedAPI.as_view(), name='embed_api'),
    re_path(r'analytics/$', AnalyticsView.as_view(), name='analytics_api'),
]

urlpatterns = api_footer_urls
