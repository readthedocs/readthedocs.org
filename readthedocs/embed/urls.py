from django.conf.urls import re_path

from .views import EmbedAPI


urlpatterns = [
    re_path(r'', EmbedAPI.as_view(), name='embed_api'),
]
