"""Add OpenTelemetryConfig model."""

import django.db.models.deletion
from django.db import migrations
from django.db import models
from django_safemigrate import Safe


class Migration(migrations.Migration):
    safe = Safe.after_deploy()
    dependencies = [
        ("analytics", "0007_index_on_pageview_date"),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpenTelemetryConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "grafana_cloud_url",
                    models.URLField(
                        blank=True,
                        help_text="Grafana Cloud Prometheus URL (e.g., https://prometheus-xxx.grafana.net/api/prom/push)",
                        max_length=512,
                        null=True,
                    ),
                ),
                (
                    "grafana_instance_id",
                    models.CharField(
                        blank=True,
                        help_text="Grafana Cloud Instance ID for authentication",
                        max_length=256,
                    ),
                ),
                (
                    "grafana_api_key",
                    models.CharField(
                        blank=True,
                        help_text="Grafana Cloud API Key (encrypted in production)",
                        max_length=512,
                    ),
                ),
                (
                    "include_path_metrics",
                    models.BooleanField(
                        default=True,
                        help_text="Include detailed path metrics (may increase cardinality). Disable for high-traffic projects.",
                    ),
                ),
                (
                    "sample_rate",
                    models.FloatField(
                        default=1.0,
                        help_text="Sample rate for metrics (0.0-1.0). Use < 1.0 for high-traffic projects.",
                    ),
                ),
                (
                    "custom_labels",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Custom labels to add to all metrics (JSON object)",
                    ),
                ),
                (
                    "export_interval_seconds",
                    models.IntegerField(
                        default=60,
                        help_text="How often to export metrics to Grafana (in seconds)",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text="Enable OpenTelemetry metrics for this project",
                    ),
                ),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otel_config",
                        to="projects.project",
                        verbose_name="Project",
                    ),
                ),
            ],
            options={
                "verbose_name": "OpenTelemetry Configuration",
                "verbose_name_plural": "OpenTelemetry Configurations",
            },
        ),
    ]
