from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from readthedocs.api.v3.models import RTDAPIKey


@admin.register(RTDAPIKey)
class RTDAPIKeyAdmin(APIKeyModelAdmin):
    raw_id_fields = ["project"]
    list_display = [*APIKeyModelAdmin.list_display, "project"]
    search_fields = [*APIKeyModelAdmin.search_fields, "project__slug"]
