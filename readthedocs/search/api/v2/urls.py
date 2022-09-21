from readthedocs.search.api.v2 import PageSearchAPIView
from django.urls import path

urlpatterns = [
    path("", PageSearchAPIView.as_view(), name="search_api"),
]
