"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf.urls import include, url

from .views.proxied import ProxiedFooterHTML

api_footer_urls = [
    url(r'footer_html/', ProxiedFooterHTML.as_view(), name='footer_html'),
]

urlpatterns = api_footer_urls
