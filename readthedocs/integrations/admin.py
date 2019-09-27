# -*- coding: utf-8 -*-

"""Integration admin models."""

from django import urls
from django.contrib import admin
from django.utils.safestring import mark_safe
from pygments.formatters import HtmlFormatter

from .models import HttpExchange, Integration


def pretty_json_field(field, description, include_styles=False):
    # There is some styling here because this is easier than reworking how the
    # admin is getting stylesheets. We only need minimal styles here, and there
    # isn't much user impact to these styles as well.
    def inner(_, obj):
        styles = ''
        if include_styles:
            formatter = HtmlFormatter(style='colorful')
            styles = '<style>' + formatter.get_style_defs() + '</style>'
        return mark_safe(
            '<div style="{}">{}</div>{}'.format(
                'float: left;',
                obj.formatted_json(field),
                styles,
            ),
        )

    inner.short_description = description
    return inner


class HttpExchangeAdmin(admin.ModelAdmin):

    """
    Admin model for HttpExchange.

    This adds some read-only display to the admin model.
    """

    readonly_fields = [
        'date',
        'status_code',
        'pretty_request_headers',
        'pretty_request_body',
        'pretty_response_headers',
        'pretty_response_body',
    ]
    fields = readonly_fields
    list_display = [
        'related_object',
        'date',
        'status_code',
        'failed_icon',
    ]

    pretty_request_headers = pretty_json_field(
        'request_headers',
        'Request headers',
        include_styles=True,
    )
    pretty_request_body = pretty_json_field(
        'request_body',
        'Request body',
    )
    pretty_response_headers = pretty_json_field(
        'response_headers',
        'Response headers',
    )
    pretty_response_body = pretty_json_field(
        'response_body',
        'Response body',
    )

    def failed_icon(self, obj):
        return not obj.failed

    failed_icon.boolean = True
    failed_icon.short_description = 'Passed'


class IntegrationAdmin(admin.ModelAdmin):

    """
    Admin model for Integration.

    Because of some problems using JSONField with admin model inlines, this
    instead just links to the queryset.
    """

    raw_id_fields = ('project',)
    search_fields = ('project__slug', 'project__name')
    readonly_fields = ['exchanges']

    def exchanges(self, obj):
        """
        Manually make an inline-ish block.

        JSONField doesn't do well with fieldsets for whatever reason. This is
        just to link to the exchanges.
        """
        url = urls.reverse(
            'admin:{}_{}_changelist'.format(
                HttpExchange._meta.app_label,  # pylint: disable=protected-access
                HttpExchange._meta.model_name,  # pylint: disable=protected-access
            ),
        )
        return mark_safe(
            '<a href="{}?{}={}">{} HTTP transactions</a>'.format(
                url,
                'integrations',
                obj.pk,
                obj.exchanges.count(),
            ),
        )

    exchanges.short_description = 'HTTP exchanges'


admin.site.register(HttpExchange, HttpExchangeAdmin)
admin.site.register(Integration, IntegrationAdmin)
