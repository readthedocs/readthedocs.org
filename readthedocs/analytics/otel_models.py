"""Models for OpenTelemetry configuration."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from readthedocs.projects.models import Project


class OpenTelemetryConfig(models.Model):
    """Per-project OpenTelemetry configuration for analytics."""

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="otel_config",
        verbose_name=_("Project"),
    )

    # Grafana Cloud configuration
    grafana_cloud_url = models.URLField(
        max_length=512,
        blank=True,
        null=True,
        help_text=_(
            "Grafana Cloud Prometheus URL (e.g., https://prometheus-xxx.grafana.net/api/prom/push)"
        ),
    )
    grafana_instance_id = models.CharField(
        max_length=256,
        blank=True,
        help_text=_("Grafana Cloud Instance ID for authentication"),
    )
    grafana_api_key = models.CharField(
        max_length=512,
        blank=True,
        help_text=_("Grafana Cloud API Key (encrypted in production)"),
    )

    # Metric collection settings
    include_path_metrics = models.BooleanField(
        default=True,
        help_text=_(
            "Include detailed path metrics (may increase cardinality). "
            "Disable for high-traffic projects."
        ),
    )
    sample_rate = models.FloatField(
        default=1.0,
        help_text=_("Sample rate for metrics (0.0-1.0). Use < 1.0 for high-traffic projects."),
    )
    custom_labels = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Custom labels to add to all metrics (JSON object)"),
    )

    # Export settings
    export_interval_seconds = models.IntegerField(
        default=60,
        help_text=_("How often to export metrics to Grafana (in seconds)"),
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(
        default=True,
        help_text=_("Enable OpenTelemetry metrics for this project"),
    )

    class Meta:
        verbose_name = _("OpenTelemetry Configuration")
        verbose_name_plural = _("OpenTelemetry Configurations")

    def __str__(self):
        return f"OpenTelemetry Config for {self.project.slug}"

    @property
    def is_configured(self):
        """Check if Grafana Cloud is properly configured."""
        return bool(
            self.enabled
            and self.grafana_cloud_url
            and self.grafana_instance_id
            and self.grafana_api_key
        )

    def get_otlp_headers(self):
        """Get OTLP headers for authentication with Grafana Cloud."""
        if not self.is_configured:
            return {}

        import base64

        # Basic auth for Grafana Cloud
        credentials = f"{self.grafana_instance_id}:{self.grafana_api_key}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
        }

    def should_sample(self):
        """Determine if this request should be sampled based on sample_rate."""
        if self.sample_rate >= 1.0:
            return True
        if self.sample_rate <= 0.0:
            return False

        import random

        return random.random() < self.sample_rate
