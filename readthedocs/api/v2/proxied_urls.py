"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf.urls import include, url

from .views.proxied import ProxiedFooterHTML
from readthedocs.search.proxied_api import ProxiedPageSearchAPIView

api_footer_urls = [
    url(r'footer_html/', ProxiedFooterHTML.as_view(), name='footer_html'),
    url(r'docsearch/$', ProxiedPageSearchAPIView.as_view(), name='doc_search'),
]

urlpatterns = api_footer_urls
