"""Audit admin."""

from django.contrib import admin

from readthedocs.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    raw_id_fields = ('user', 'project')
    search_fields = ('log_user_username', 'browser', 'log_project_slug')
    list_filter = ('log_user_username', 'ip', 'log_project_slug', 'action')
    list_display = (
        'action',
        'log_user_username',
        'log_project_slug',
        'ip',
        'browser',
        'resource',
    )
