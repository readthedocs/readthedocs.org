"""Filters used in project dashboard."""

import structlog
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet

from readthedocs.builds.constants import (
    BUILD_FINAL_STATES,
    BUILD_STATE_FINISHED,
    EXTERNAL,
)

log = structlog.get_logger(__name__)


class BuildListFilter(FilterSet):

    """Project build list dashboard filter."""

    STATE_ACTIVE = "active"
    STATE_SUCCESS = "succeeded"
    STATE_FAILED = "failed"

    STATE_CHOICES = (
        (STATE_ACTIVE, _("Active")),
        (STATE_SUCCESS, _("Build successful")),
        (STATE_FAILED, _("Build failed")),
    )

    TYPE_NORMAL = "normal"
    TYPE_EXTERNAL = "external"
    TYPE_CHOICES = (
        (TYPE_NORMAL, _("Normal")),
        (TYPE_EXTERNAL, _("Pull/merge request")),
    )

    # Attribute filter fields
    version = CharFilter(field_name="version__slug", widget=HiddenInput)
    state = ChoiceFilter(
        label=_("State"),
        choices=STATE_CHOICES,
        empty_label=_("Any"),
        method="get_state",
    )
    version__type = ChoiceFilter(
        label=_("Type"),
        choices=TYPE_CHOICES,
        empty_label=_("Any"),
        method="get_version_type",
    )

    def get_state(self, queryset, _, value):
        if value == self.STATE_ACTIVE:
            queryset = queryset.exclude(state__in=BUILD_FINAL_STATES)
        elif value == self.STATE_SUCCESS:
            queryset = queryset.filter(state=BUILD_STATE_FINISHED, success=True)
        elif value == self.STATE_FAILED:
            queryset = queryset.filter(
                state__in=BUILD_FINAL_STATES,
                success=False,
            )
        return queryset

    def get_version_type(self, queryset, _, value):
        if value == self.TYPE_NORMAL:
            queryset = queryset.exclude(version__type=EXTERNAL)
        elif value == self.TYPE_EXTERNAL:
            queryset = queryset.filter(version__type=EXTERNAL)
        return queryset
