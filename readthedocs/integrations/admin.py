"""Integration admin models."""

from django import urls
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from pygments.formatters import HtmlFormatter

from .models import HttpExchange
from .models import Integration


def pretty_json_field(field, description, include_styles=False):
    # There is some styling here because this is easier than reworking how the
    # admin is getting stylesheets. We only need minimal styles here, and there
    # isn't much user impact to these styles as well.
    def inner(_, obj):
        styles = ""
        if include_styles:
            formatter = HtmlFormatter(style="colorful")
            styles = "<style>" + formatter.get_style_defs() + "</style>"
        return mark_safe(
            '<div style="{}">{}</div>{}'.format(
                "float: left;",
                obj.formatted_json(field),
                styles,
            ),
        )

    inner.short_description = description
    return inner


@admin.register(HttpExchange)
class HttpExchangeAdmin(admin.ModelAdmin):
    """
    Admin model for HttpExchange.

    This adds some read-only display to the admin model.
    """

    readonly_fields = [
        "date",
        "status_code",
        "pretty_request_headers",
        "pretty_request_body",
        "pretty_response_headers",
        "pretty_response_body",
    ]
    fields = readonly_fields
    search_fields = ("integrations__project__slug", "integrations__project__name")
    list_display = [
        "related_object",
        "date",
        "status_code",
        "failed_icon",
    ]

    pretty_request_headers = pretty_json_field(
        "request_headers",
        "Request headers",
        include_styles=True,
    )
    pretty_request_body = pretty_json_field(
        "request_body",
        "Request body",
    )
    pretty_response_headers = pretty_json_field(
        "response_headers",
        "Response headers",
    )
    pretty_response_body = pretty_json_field(
        "response_body",
        "Response body",
    )

    @admin.display(
        description="Passed",
        boolean=True,
    )
    def failed_icon(self, obj):
        return not obj.failed


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    """
    Admin model for Integration.

    Because of some problems using JSONField with admin model inlines, this
    instead just links to the queryset.
    """

    raw_id_fields = ("project",)
    search_fields = ("project__slug", "project__name")
    readonly_fields = ["exchanges"]

    # TODO: review this now that we are using official Django's JSONField
    @admin.display(description="HTTP exchanges")
    def exchanges(self, obj):
        """
        Manually make an inline-ish block.

        JSONField doesn't do well with fieldsets for whatever reason. This is
        just to link to the exchanges.
        """
        url = urls.reverse(
            "admin:{}_{}_changelist".format(
                HttpExchange._meta.app_label,
                HttpExchange._meta.model_name,
            ),
        )
        return format_html(
            '<a href="{}?{}={}">{} HTTP transactions</a>',
            url,
            "integrations__pk",
            obj.pk,
            obj.exchanges.count(),
        )
