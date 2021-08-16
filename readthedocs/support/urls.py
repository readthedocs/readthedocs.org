from django.conf.urls import url

from readthedocs.support.views import FrontAppWebhook

urlpatterns = [
    url(r'^frontapp-webhook/$', FrontAppWebhook.as_view(), name='frontapp_webhook'),
]
