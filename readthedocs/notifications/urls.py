"""Renames for messages_extends URLs"""

from django.conf.urls import url

from .views import notification_dismiss, notification_dismiss_all


urlpatterns = [
    url(r'^dismiss/(?P<message_id>\d+)/$', notification_dismiss,
        name='notification_dismiss'),
    url(r'^dismiss/all/$', notification_dismiss_all,
        name='notification_dismiss_all'),
]
