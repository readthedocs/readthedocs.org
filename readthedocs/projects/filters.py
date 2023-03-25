"""Filters used in project dashboard."""

import structlog
from django.db.models import Count, F, Max
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet, OrderingFilter

log = structlog.get_logger(__name__)


class VersionSortOrderingFilter(OrderingFilter):

    """
    Version list sort ordering django_filters filter.

    Django-filter is highly opionated, and the default model filters do not work
    well with empty/null values in the filter choices. In our case, empty/null
    values are used for a default query. So, to make this work, we will use a
    custom filter, instead of an automated model filter.

    The empty/None value is used to provide both a default value to the filter
    (when there is no ``sort`` query param), but also provide an option that is
    manually selectable (``?sort=relevance``). We can't do this with the default
    filter, because result would be params like ``?sort=None``.
    """

    SORT_BUILD_COUNT = "build_count"
    SORT_BUILD_DATE = "build_date"
    SORT_NAME = "name"

    def __init__(self, *args, **kwargs):
        # The default filtering operation will be `-recent`, so we omit it
        # from choices to avoid showing it on the list twice.
        kwargs.setdefault("empty_label", _("Recently built"))
        kwargs.setdefault(
            "choices",
            (
                ("-" + self.SORT_BUILD_DATE, _("Least recently built")),
                ("-" + self.SORT_BUILD_COUNT, _("Frequently built")),
                (self.SORT_BUILD_COUNT, _("Least frequently built")),
                (self.SORT_NAME, _("Name")),
                ("-" + self.SORT_NAME, _("Name (descending)")),
            ),
        )
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        # This is where we use the None value for this custom filter. This
        # doesn't work with a standard model filter. Note: ``value`` is always
        # an iterable, but can be empty.
        if not value:
            value = [self.SORT_BUILD_DATE]

        annotations = {}
        order_bys = []
        for field_ordered in value:
            field = field_ordered.lstrip("-")

            if field == self.SORT_BUILD_DATE:
                annotations[self.SORT_BUILD_DATE] = Max("builds__date")
            elif field == self.SORT_BUILD_COUNT:
                annotations[self.SORT_BUILD_COUNT] = Count("builds")
            elif field == self.SORT_NAME:
                # Alias field name here, as ``OrderingFilter`` was having trouble
                # doing this with it's native field mapping
                annotations[self.SORT_NAME] = F("verbose_name")

            if field_ordered == self.SORT_BUILD_DATE:
                order_bys.append(F(field).desc(nulls_last=True))
            elif field_ordered == "-" + self.SORT_BUILD_DATE:
                order_bys.append(F(field).asc(nulls_first=True))
            else:
                order_bys.append(field_ordered)

        return qs.annotate(**annotations).order_by(*order_bys)


class ProjectSortOrderingFilter(OrderingFilter):

    """
    Project list sort ordering django_filters filter.

    Django-filter is highly opionated, and the default model filters do not work
    well with empty/null values in the filter choices. In our case, empty/null
    values are used for a default query. So, to make this work, we will use a
    custom filter, instead of an automated model filter.
    """

    SORT_NAME = "name"
    SORT_MODIFIED_DATE = "modified_date"
    SORT_BUILD_DATE = "build_date"
    SORT_BUILD_COUNT = "build_count"

    def __init__(self, *args, **kwargs):
        # The default filtering operation will be `name`, so we omit it
        # from choices to avoid showing it on the list twice.
        kwargs.setdefault("empty_label", _("Recently built"))
        kwargs.setdefault(
            "choices",
            (
                ("-" + self.SORT_BUILD_DATE, _("Least recently built")),
                ("-" + self.SORT_BUILD_COUNT, _("Frequently built")),
                (self.SORT_BUILD_COUNT, _("Least frequently built")),
                ("-" + self.SORT_MODIFIED_DATE, _("Recently modified")),
                (self.SORT_MODIFIED_DATE, _("Least recently modified")),
                (self.SORT_NAME, _("Name")),
                ("-" + self.SORT_NAME, _("Name (descending)")),
            ),
        )
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        # This is where we use the None value from the custom filter
        if not value:
            value = [self.SORT_BUILD_DATE]

        annotations = {}
        order_bys = []
        for field_ordered in value:
            field = field_ordered.lstrip("-")

            if field == self.SORT_BUILD_DATE:
                annotations[self.SORT_BUILD_DATE] = Max("builds__date")
            elif field == self.SORT_BUILD_COUNT:
                annotations[self.SORT_BUILD_COUNT] = Count("builds")

            if field_ordered == self.SORT_BUILD_DATE:
                order_bys.append(F(field).desc(nulls_last=True))
            elif field_ordered == "-" + self.SORT_BUILD_DATE:
                order_bys.append(F(field).asc(nulls_first=True))
            else:
                order_bys.append(field_ordered)

        return qs.annotate(**annotations).order_by(*order_bys)


class ProjectListFilterSet(FilterSet):

    """
    Project list filter set for project list view.

    This filter set enables list view sorting using a custom filter, and
    provides search-as-you-type lookup filter as well.
    """

    project = CharFilter(field_name="slug", widget=HiddenInput)
    sort = ProjectSortOrderingFilter(
        field_name="sort",
        label=_("Sort by"),
    )


class ProjectVersionListFilterSet(FilterSet):

    """
    Filter and sorting for project version listing page.

    This is used from the project versions list view page to provide filtering
    and sorting to the version list and search UI. It is normally instantiated
    with an included queryset, which provides user project authorization.
    """

    VISIBILITY_HIDDEN = "hidden"
    VISIBILITY_VISIBLE = "visible"

    VISIBILITY_CHOICES = (
        ("hidden", _("Hidden versions")),
        ("visible", _("Visible versions")),
    )

    PRIVACY_CHOICES = (
        ("public", _("Public versions")),
        ("private", _("Private versions")),
    )

    # Attribute filter fields
    version = CharFilter(field_name="slug", widget=HiddenInput)
    privacy = ChoiceFilter(
        field_name="privacy_level",
        label=_("Privacy"),
        choices=PRIVACY_CHOICES,
        empty_label=_("Any"),
    )
    # This field looks better as ``visibility=hidden`` than it does
    # ``hidden=true``, otherwise we could use a BooleanFilter instance here
    # instead
    visibility = ChoiceFilter(
        field_name="hidden",
        label=_("Visibility"),
        choices=VISIBILITY_CHOICES,
        method="get_visibility",
        empty_label=_("Any"),
    )

    sort = VersionSortOrderingFilter(
        field_name="sort",
        label=_("Sort by"),
    )

    def get_visibility(self, queryset, *, value):
        if value == self.VISIBILITY_HIDDEN:
            return queryset.filter(hidden=True)
        if value == self.VISIBILITY_VISIBLE:
            return queryset.filter(hidden=False)
        return queryset
