"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.urls import path

from readthedocs.api.v3.proxied_views import ProxiedEmbedAPI
from readthedocs.search.api.v3.views import ProxiedSearchAPI


api_proxied_urls = [
    path("embed/", ProxiedEmbedAPI.as_view(), name="embed_api_v3"),
    path("search/", ProxiedSearchAPI.as_view(), name="search_api_v3"),
]

urlpatterns = api_proxied_urls
