"""Filters used in project dashboard."""

import structlog
from django.utils.translation import gettext_lazy as _
from django_filters import ChoiceFilter

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import INTERNAL
from readthedocs.core.filters import FilteredModelChoiceFilter
from readthedocs.core.filters import ModelFilterSet


log = structlog.get_logger(__name__)


class BuildListFilter(ModelFilterSet):
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
    version__slug = FilteredModelChoiceFilter(
        label=_("Version"),
        empty_label=_("All versions"),
        to_field_name="slug",
        queryset_method="get_version_queryset",
        method="get_version",
    )
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

    def __init__(self, *args, project=None, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def get_version(self, queryset, _, version):
        return queryset.filter(version__slug=version.slug)

    def get_version_queryset(self):
        # Copied from the version listing view. We need this here as this is
        # what allows the build version list to populate. Otherwise the
        # ``all()`` queryset method is used.
        return self.project.versions(manager=INTERNAL).public(
            user=self.request.user,
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
