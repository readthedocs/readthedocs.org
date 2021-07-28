from django.contrib import admin

from readthedocs.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    search_fields = ('log_username', 'browser', 'project__slug')
    list_filter = ('log_username', 'ip', 'project', 'action')
    list_display = (
        'action',
        'log_username',
        'project',
        'ip',
        'browser',
        'resource',
    )
