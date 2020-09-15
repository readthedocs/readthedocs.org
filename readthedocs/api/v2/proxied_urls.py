"""
Proxied API URLs.

Served from the same domain docs are served,
so they can make use of features that require to have access to their cookies.
"""

from django.conf import settings
from django.conf.urls import include, url

from .views.proxied import ProxiedFooterHTML
from readthedocs.search.proxied_api import ProxiedPageSearchAPIView

api_footer_urls = [
    url(r'footer_html/', ProxiedFooterHTML.as_view(), name='footer_html'),
    url(r'docsearch/$', ProxiedPageSearchAPIView.as_view(), name='doc_search'),
    url(r'search/$', ProxiedPageSearchAPIView.as_view(new_api=True), name='search_api'),
]

urlpatterns = api_footer_urls

if 'readthedocsext.embed' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'embed/', include('readthedocsext.embed.urls'))
    ]
