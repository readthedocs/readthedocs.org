"""Telemetry admin."""


from django.contrib import admin

from readthedocs.core.utils.admin import pretty_json_field
from readthedocs.telemetry.models import BuildData


@admin.register(BuildData)
class BuildDataAdmin(admin.ModelAdmin):

    fields = ("created", "modified", "pretty_data")
    readonly_fields = (
        "created",
        "modified",
        "pretty_data",
    )

    # pylint: disable=no-self-use
    def pretty_data(self, instance):
        return pretty_json_field(instance, "data")
