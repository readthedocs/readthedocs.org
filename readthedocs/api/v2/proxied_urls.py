"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.urls import path

from readthedocs.analytics.proxied_api import AnalyticsView
from readthedocs.api.v2.views.proxied import ProxiedEmbedAPI, ProxiedFooterHTML
from readthedocs.search.api.v2.views import ProxiedPageSearchAPIView

api_footer_urls = [
    path("footer_html/", ProxiedFooterHTML.as_view(), name="footer_html"),
    path("search/", ProxiedPageSearchAPIView.as_view(), name="search_api"),
    path("embed/", ProxiedEmbedAPI.as_view(), name="embed_api"),
    path("analytics/", AnalyticsView.as_view(), name="analytics_api"),
]

urlpatterns = api_footer_urls
