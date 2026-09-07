from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from readthedocs.api.v2.models import BuildAPIKey


@admin.register(BuildAPIKey)
class BuildAPIKeyAdmin(APIKeyModelAdmin):
    raw_id_fields = ["project"]
    list_display = [*APIKeyModelAdmin.list_display, "project", "internal", "permission_level"]
    list_filter = [*APIKeyModelAdmin.list_filter, "internal", "permission_level"]
    search_fields = [*APIKeyModelAdmin.search_fields, "project__slug"]
