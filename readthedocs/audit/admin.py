"""Audit admin."""

from django.contrib import admin

from readthedocs.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    raw_id_fields = ("user", "project", "organization")
    search_fields = (
        "log_user_username",
        "ip",
        "browser",
        "log_project_slug",
        "log_organization_slug",
    )
    list_filter = ("action",)
    list_display = (
        "action",
        "log_user_username",
        "log_project_slug",
        "log_organization_slug",
        "ip",
        "browser",
        "resource",
    )
