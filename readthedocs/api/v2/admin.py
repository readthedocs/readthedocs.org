from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin

from readthedocs.api.v2.models import BuildAPIKey


@admin.register(BuildAPIKey)
class BuildAPIKeyAdmin(APIKeyModelAdmin):
    raw_id_fields = ["project"]
    search_fields = [*APIKeyModelAdmin.search_fields, "project__slug"]
