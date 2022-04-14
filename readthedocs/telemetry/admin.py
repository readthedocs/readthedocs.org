"""Telemetry admin."""


from django.contrib import admin

from readthedocs.core.utils.admin import pretty_json_field
from readthedocs.telemetry.models import BuildData


@admin.register(BuildData)
class BuildDataAdmin(admin.ModelAdmin):

    fields = ("pretty_data",)
    readonly_fields = ("pretty_data",)

    # pylint: disable=no-self-use
    def pretty_data(self, instance):
        return pretty_json_field(instance, "data")
