"""Invitations admin."""

from django.contrib import admin

from readthedocs.invitations.models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    search_fields = (
        "from_user__username",
        "to_user__username",
        "to_user__email",
        "to_email",
    )
    list_display = (
        "pk",
        "from_user",
        "to_user",
        "to_email",
        "object_type",
        "object",
    )
    raw_id_fields = (
        "from_user",
        "to_user",
    )
