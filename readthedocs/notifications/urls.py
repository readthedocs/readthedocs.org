"""Renames for messages_extends URLs."""

from django.urls import path
from messages_extends.views import message_mark_all_read, message_mark_read

urlpatterns = [
    path(
        "dismiss/<int:message_id>/",
        message_mark_read,
        name="message_mark_read",
    ),
    path(
        "dismiss/all/",
        message_mark_all_read,
        name="message_mark_all_read",
    ),
]
