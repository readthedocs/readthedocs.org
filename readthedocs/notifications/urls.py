"""Renames for messages_extends URLs."""

from django.conf.urls import re_path
from messages_extends.views import message_mark_all_read, message_mark_read

urlpatterns = [
    re_path(
        r'^dismiss/(?P<message_id>\d+)/$',
        message_mark_read,
        name='message_mark_read',
    ),
    re_path(
        r'^dismiss/all/$',
        message_mark_all_read,
        name='message_mark_all_read',
    ),
]
