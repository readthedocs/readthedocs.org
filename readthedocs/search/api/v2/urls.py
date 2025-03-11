from django.urls import path

from readthedocs.search.api.v2.views import PageSearchAPIView


urlpatterns = [
    path("", PageSearchAPIView.as_view(), name="search_api"),
]
