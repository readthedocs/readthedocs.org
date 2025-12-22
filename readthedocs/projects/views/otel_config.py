"""Views for OpenTelemetry configuration."""

import json

import structlog
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from vanilla import UpdateView

from readthedocs.analytics.otel_models import OpenTelemetryConfig
from readthedocs.projects.models import Project
from readthedocs.projects.views.private import ProjectMixin


log = structlog.get_logger(__name__)


class OpenTelemetryConfigView(ProjectMixin, UpdateView):
    """View for configuring OpenTelemetry for a project."""

    def get(self, request, project_slug):
        """Display the OpenTelemetry configuration form."""
        project = get_object_or_404(Project, slug=project_slug)
        # self.check_project_permission(request, project)

        otel_config, _ = OpenTelemetryConfig.objects.get_or_create(project=project)

        context = {
            "project": project,
            "otel_config": otel_config,
        }
        return render(request, "projects/otel_config.html", context)

    def post(self, request, project_slug):
        """Handle OpenTelemetry configuration form submission."""
        project = get_object_or_404(Project, slug=project_slug)
        self.check_project_permission(request, project)

        action = request.POST.get("action", "save")

        otel_config, _ = OpenTelemetryConfig.objects.get_or_create(project=project)

        # Get form data
        enabled = request.POST.get("enabled") == "on"
        grafana_cloud_url = request.POST.get("grafana_cloud_url", "").strip()
        grafana_instance_id = request.POST.get("grafana_instance_id", "").strip()
        grafana_api_key = request.POST.get("grafana_api_key", "").strip()
        include_path_metrics = request.POST.get("include_path_metrics") == "on"
        sample_rate = request.POST.get("sample_rate", "1.0")
        export_interval_seconds = request.POST.get("export_interval_seconds", "60")
        custom_labels = request.POST.get("custom_labels", "{}")

        # Validate enabled state
        if enabled:
            if not grafana_cloud_url or not grafana_instance_id or not grafana_api_key:
                messages.error(
                    request,
                    _("Grafana Cloud credentials are required when OpenTelemetry is enabled."),
                )
                context = {
                    "project": project,
                    "otel_config": otel_config,
                }
                return render(request, "projects/otel_config.html", context, status=400)

        # Validate sample rate
        try:
            sample_rate = float(sample_rate)
            if not 0.0 <= sample_rate <= 1.0:
                raise ValueError("Sample rate must be between 0.0 and 1.0")
        except (ValueError, TypeError):
            messages.error(
                request,
                _("Invalid sample rate: must be a number between 0.0 and 1.0"),
            )
            context = {
                "project": project,
                "otel_config": otel_config,
            }
            return render(request, "projects/otel_config.html", context, status=400)

        # Validate export interval
        try:
            export_interval_seconds = int(export_interval_seconds)
            if not 10 <= export_interval_seconds <= 300:
                raise ValueError("Export interval must be between 10 and 300 seconds")
        except (ValueError, TypeError):
            messages.error(
                request,
                _("Invalid export interval: must be between 10 and 300 seconds"),
            )
            context = {
                "project": project,
                "otel_config": otel_config,
            }
            return render(request, "projects/otel_config.html", context, status=400)

        # Validate custom labels JSON
        try:
            custom_labels_dict = json.loads(custom_labels) if custom_labels else {}
            if not isinstance(custom_labels_dict, dict):
                raise ValueError("Custom labels must be a JSON object")
        except json.JSONDecodeError:
            messages.error(
                request,
                _("Invalid custom labels: must be valid JSON"),
            )
            context = {
                "project": project,
                "otel_config": otel_config,
            }
            return render(request, "projects/otel_config.html", context, status=400)

        # Handle test connection
        if action == "test":
            if otel_config.is_configured:
                try:
                    # Import here to avoid circular imports
                    from readthedocs.analytics.telemetry import analytics_metrics

                    # Record a test metric
                    analytics_metrics.record_page_view(
                        project=project,
                        version_slug="test",
                        path="/test",
                        status_code=200,
                        is_external=False,
                    )
                    messages.success(
                        request,
                        _(
                            "Test metric sent successfully! Check Grafana Cloud for metrics arrival."
                        ),
                    )
                except Exception as e:
                    log.exception("Failed to send test metric", error=str(e))
                    messages.error(
                        request,
                        _("Failed to send test metric: {}").format(str(e)),
                    )
            else:
                messages.error(
                    request,
                    _("Configuration is incomplete. Please fill in all required fields."),
                )

        else:
            # Save configuration
            otel_config.enabled = enabled
            otel_config.grafana_cloud_url = grafana_cloud_url
            otel_config.grafana_instance_id = grafana_instance_id
            otel_config.grafana_api_key = grafana_api_key
            otel_config.include_path_metrics = include_path_metrics
            otel_config.sample_rate = sample_rate
            otel_config.export_interval_seconds = export_interval_seconds
            otel_config.custom_labels = custom_labels_dict
            otel_config.save()

            if enabled and otel_config.is_configured:
                messages.success(
                    request,
                    _(
                        "OpenTelemetry configuration saved successfully! "
                        "Metrics will be exported to Grafana Cloud."
                    ),
                )
            elif enabled:
                messages.warning(
                    request,
                    _("Configuration saved but is incomplete. Please verify your credentials."),
                )
            else:
                messages.success(
                    request,
                    _("OpenTelemetry is now disabled for this project."),
                )

        # Redirect to get page to show messages
        return redirect("projects_otel_config", project_slug=project.slug)
