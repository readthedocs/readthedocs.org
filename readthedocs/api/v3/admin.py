from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from readthedocs.api.v3.models import RTDAPIKey


@admin.register(RTDAPIKey)
class RTDAPIKeyAdmin(APIKeyModelAdmin):
    raw_id_fields = ["project", "created_by"]
    list_display = [*APIKeyModelAdmin.list_display, "project"]
    search_fields = [*APIKeyModelAdmin.search_fields, "project__slug"]

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
