from django.urls import path

from .views import EmbedAPI


urlpatterns = [
    path("", EmbedAPI.as_view(), name="embed_api"),
]
