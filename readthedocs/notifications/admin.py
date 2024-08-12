"""Notifications admin."""

from django.contrib import admin

from readthedocs.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    search_fields = ("message_id",)
    list_filter = ("state",)
    list_display = (
        "id",
        "message_id",
        "attached_to_content_type",
        "state",
    )
