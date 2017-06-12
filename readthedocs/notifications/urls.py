"""Renames for messages_extends URLs"""

from __future__ import absolute_import
from django.conf.urls import url

from messages_extends.views import message_mark_read, message_mark_all_read


urlpatterns = [
    url(r'^dismiss/(?P<message_id>\d+)/$', message_mark_read,
        name='message_mark_read'),
    url(r'^dismiss/all/$', message_mark_all_read,
        name='message_mark_all_read'),
]
