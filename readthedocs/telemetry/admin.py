"""Telemetry admin."""
# pylint: disable=no-self-use

from django.contrib import admin

from readthedocs.core.utils.admin import pretty_json_field
from readthedocs.telemetry.models import BuildData


@admin.register(BuildData)
class BuildDataAdmin(admin.ModelAdmin):

    """Admin class for BuildData model."""

    fields = ("created", "modified", "pretty_data")
    readonly_fields = (
        "created",
        "modified",
        "pretty_data",
    )
    list_display = ("created", "_get_project", "_get_version", "_get_build")

    @admin.display(description="Project")
    def _get_project(self, obj):
        return obj.data.get("project", {}).get("slug")

    @admin.display(description="Version")
    def _get_version(self, obj):
        return obj.data.get("version", {}).get("slug")

    @admin.display(description="Build")
    def _get_build(self, obj):
        return obj.data.get("build", {}).get("id")

    # pylint: disable=no-self-use
    def pretty_data(self, instance):
        return pretty_json_field(instance, "data")
