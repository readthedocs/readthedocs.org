from django.urls import path

from .views import UploadCompleteView, UploadInitiateView

urlpatterns = [
    path(
        "upload/initiate/",
        UploadInitiateView.as_view(),
        name="upload-initiate",
    ),
    path(
        "upload/complete/",
        UploadCompleteView.as_view(),
        name="upload-complete",
    ),
]
