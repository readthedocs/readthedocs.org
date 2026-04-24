from django.urls import path

from readthedocs.search.api.v3.views import SearchAPI


urlpatterns = [
    path("", SearchAPI.as_view(), name="search_api_v3"),
]
