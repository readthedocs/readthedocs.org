"""OpenTelemetry configuration for analytics."""

import structlog
from django.conf import settings
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


log = structlog.get_logger(__name__)


class AnalyticsMetrics:
    """OpenTelemetry metrics for analytics tracking."""

    def __init__(self):
        self._meter = None
        self._page_view_counter = None
        self._page_view_histogram = None
        self._enabled = False

    def initialize(self):
        """Initialize OpenTelemetry metrics."""
        if not settings.OTEL_ANALYTICS_ENABLED:
            log.info("OpenTelemetry analytics disabled")
            return

        try:
            # Create resource with service information
            resource = Resource.create(
                {
                    "service.name": "readthedocs-analytics",
                    "service.namespace": settings.OTEL_SERVICE_NAMESPACE,
                    "deployment.environment": settings.OTEL_ENVIRONMENT,
                }
            )

            # Configure OTLP exporter for Grafana Cloud
            exporter = OTLPMetricExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                headers=settings.OTEL_EXPORTER_OTLP_HEADERS,
            )

            # Create metric reader with export interval
            reader = PeriodicExportingMetricReader(
                exporter,
                export_interval_millis=settings.OTEL_METRIC_EXPORT_INTERVAL,
            )

            # Create meter provider
            provider = MeterProvider(
                resource=resource,
                metric_readers=[reader],
            )

            # Set global meter provider
            metrics.set_meter_provider(provider)

            # Get meter instance
            self._meter = metrics.get_meter(
                "readthedocs.analytics",
                version="1.0.0",
            )

            # Create metrics instruments
            self._page_view_counter = self._meter.create_counter(
                name="rtd.pageviews.total",
                description="Total number of page views",
                unit="1",
            )

            self._page_view_histogram = self._meter.create_histogram(
                name="rtd.pageviews.by_path",
                description="Page views distribution by path",
                unit="1",
            )

            self._enabled = True
            log.info("OpenTelemetry analytics initialized successfully")

        except Exception as e:
            log.exception("Failed to initialize OpenTelemetry analytics", error=str(e))
            self._enabled = False

    def is_enabled_for_project(self, project):
        """Check if OpenTelemetry is enabled for a specific project."""
        from readthedocs.projects.models import Feature

        if not self._enabled:
            return False

        # Check if project has OpenTelemetry enabled via feature flag
        return project.has_feature(Feature.ENABLE_OTEL_ANALYTICS)

    def record_page_view(
        self,
        project,
        version_slug,
        path,
        status_code,
        is_external=False,
    ):
        """Record a page view metric."""
        if not self.is_enabled_for_project(project):
            return

        try:
            # Get project-specific configuration
            otel_config = project.otel_config

            # Common attributes for all metrics
            attributes = {
                "project": project.slug,
                "version": version_slug or "unknown",
                "status": str(status_code),
                "is_external": str(is_external),
            }

            # Add custom labels from project configuration
            if otel_config and otel_config.custom_labels:
                attributes.update(otel_config.custom_labels)

            # Record counter
            self._page_view_counter.add(1, attributes=attributes)

            # Record histogram with path-specific attributes if enabled
            if not otel_config or otel_config.include_path_metrics:
                path_attributes = {
                    **attributes,
                    "path": path,
                }
                self._page_view_histogram.record(1, attributes=path_attributes)

        except Exception as e:
            log.warning(
                "Failed to record page view metric",
                error=str(e),
                project=project.slug,
            )


# Global instance
analytics_metrics = AnalyticsMetrics()
