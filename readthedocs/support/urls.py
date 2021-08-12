from django.conf.urls import url

from readthedocs.support.views import FrontWebhook

urlpatterns = [
    url(r'^front-webhook/$', FrontWebhook.as_view(), name='front_webhook'),
]
