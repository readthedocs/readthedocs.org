"""Models for OpenTelemetry configuration."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.projects.models import Project


class OpenTelemetryConfig(TimeStampedModel):
    """Per-project OpenTelemetry configuration for analytics."""

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="otel_config",
        verbose_name=_("Project"),
    )

    enabled = models.BooleanField(
        default=False,
        help_text=_("Enable OpenTelemetry metrics for this project"),
    )

    endpoint_url = models.URLField(
        max_length=1024,
        blank=True,
        null=True,
        help_text=_("Endpoint URL (e.g., https://prometheus-xxx.grafana.net/otlp/v1/metrics)"),
    )
    api_key = models.CharField(
        max_length=512,
        blank=True,
        help_text=_("Grafana Cloud API Key (encrypted in production)"),
    )

    class Meta:
        verbose_name = _("OpenTelemetry Configuration")
        verbose_name_plural = _("OpenTelemetry Configurations")

    def __str__(self):
        return f"OpenTelemetry Config for {self.project.slug}"
