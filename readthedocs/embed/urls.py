from django.conf.urls import url

from .views import EmbedAPI


urlpatterns = [
    url(r'', EmbedAPI.as_view(), name='api_embed'),
]
