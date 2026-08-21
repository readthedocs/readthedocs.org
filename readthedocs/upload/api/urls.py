from django.urls import path

from readthedocs.upload.api.views import UploadCompleteView
from readthedocs.upload.api.views import UploadInitiateView


urlpatterns = [
    path(
        "initiate/",
        UploadInitiateView.as_view(),
        name="upload-api-initiate",
    ),
    path(
        "complete/",
        UploadCompleteView.as_view(),
        name="upload-api-complete",
    ),
]
