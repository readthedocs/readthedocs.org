"""OpenTelemetry configuration for analytics."""

import structlog
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


log = structlog.get_logger(__name__)


class AnalyticsMetrics:
    """OpenTelemetry metrics for analytics tracking."""

    def __init__(self, project):
        self.meter = None
        self.page_view_counter = None
        self.page_view_histogram = None
        self.enabled = False

        try:
            # Create resource with service information
            resource = Resource.create(
                # Load these from `Project.otel_config`
                {
                    "service.name": project.slug,
                    "service.namespace": "readthedocs-analytics",
                }
            )

            # Configure OTLP exporter for Grafana Cloud
            # TODO: load them from `Project.otel_config`
            exporter = OTLPMetricExporter(
                endpoint=project.otel_config.endpoint_url,
                headers={"Authorization": f"Basic {project.otel_config.api_key}"},  #
            )

            # Create metric reader with export interval
            reader = PeriodicExportingMetricReader(
                exporter,
                export_interval_millis=60000,  # 60 seconds
            )

            # Create meter provider
            provider = MeterProvider(
                resource=resource,
                metric_readers=[reader],
            )

            # Set global meter provider
            metrics.set_meter_provider(provider)

            self.meter = metrics.get_meter(
                "readthedocs.analytics",
                version="1.0.0",
            )

            # Create metrics instruments
            self.page_view_counter = self.meter.create_counter(
                name="readthedocs.pageviews.total",
                description="Total number of page views",
                unit="1",
            )

            log.debug("OpenTelemetry analytics initialized successfully")

        except Exception:
            log.exception("Failed to initialize OpenTelemetry analytics")

    def record_page_view(
        self,
        project,
        version,
        filename,
        path,
        status,
    ):
        """Record a page view metric."""

        try:
            attributes = {
                "project": project.slug,
                "version": version.slug,
                "filename": filename,
                "path": path,
                "status": status,
            }

            self.page_view_counter.add(1, attributes=attributes)

        except Exception as e:
            log.warning(
                "Failed to record page view metric",
                error=str(e),
                project=project.slug,
            )
