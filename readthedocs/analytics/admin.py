"""Analytics Admin classes."""

from django.contrib import admin

from .models import PageView
from .otel_models import OpenTelemetryConfig


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    raw_id_fields = ("project", "version")
    list_display = ("project", "version", "path", "view_count", "date")
    search_fields = ("project__slug", "version__slug", "path")
    readonly_fields = ("date",)
    list_select_related = ("project", "version", "version__project")


@admin.register(OpenTelemetryConfig)
class OpenTelemetryConfigAdmin(admin.ModelAdmin):
    """Admin for OpenTelemetryConfig model."""

    list_display = [
        "project",
        "enabled",
        "is_configured",
        "sample_rate",
        "include_path_metrics",
        "updated_at",
    ]
    list_filter = ["enabled", "include_path_metrics"]
    search_fields = ["project__slug"]
    raw_id_fields = ["project"]
    readonly_fields = ["created_at", "updated_at", "is_configured"]

    fieldsets = (
        (
            "Project",
            {
                "fields": ("project", "enabled"),
            },
        ),
        (
            "Grafana Cloud Configuration",
            {
                "fields": (
                    "grafana_cloud_url",
                    "grafana_instance_id",
                    "grafana_api_key",
                ),
                "description": "Configure Grafana Cloud for metrics export",
            },
        ),
        (
            "Metric Collection Settings",
            {
                "fields": (
                    "include_path_metrics",
                    "sample_rate",
                    "custom_labels",
                    "export_interval_seconds",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("is_configured", "created_at", "updated_at"),
            },
        ),
    )

    @admin.display(
        description="Configured",
        boolean=True,
    )
    def is_configured(self, obj):
        """Show if configuration is complete."""
        return obj.is_configured
