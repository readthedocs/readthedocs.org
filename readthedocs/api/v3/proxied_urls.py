"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf.urls import url

from readthedocs.api.v3.proxied_views import ProxiedEmbedAPI

api_proxied_urls = [
    url(r'embed/', ProxiedEmbedAPI.as_view(), name='embed_api_v3'),
]

urlpatterns = api_proxied_urls
