"""Filters used in organization dashboard."""

import structlog
from django.db.models import F
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _
from django_filters import CharFilter, FilterSet, OrderingFilter

log = structlog.get_logger(__name__)


class OrganizationSortOrderingFilter(OrderingFilter):

    """Organization list sort ordering django_filters filter."""

    SORT_NAME = "name"
    SORT_CREATE_DATE = "pub_date"

    def __init__(self, *args, **kwargs):
        # The default filtering operation will be `name`, so we omit it
        # from choices to avoid showing it on the list twice.
        kwargs.setdefault("empty_label", _("Name"))
        kwargs.setdefault(
            "choices",
            (
                ("-" + self.SORT_CREATE_DATE, _("Recently created")),
                (self.SORT_CREATE_DATE, _("Least recently created")),
                (self.SORT_NAME, _("Name")),
                ("-" + self.SORT_NAME, _("Name (descending)")),
            ),
        )
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        # We use the None value from the custom filter, which django-filters is
        # a bit opinionated about. This is an explicit check for ``None``
        # instead of setting some default value, purposely to make display of
        # the unused/default filter correct.
        if not value:
            value = [self.SORT_NAME]

        order_bys = []
        for field_ordered in value:
            field = field_ordered.lstrip("-")

            if field_ordered == self.SORT_CREATE_DATE:
                order_bys.append(F(field).desc(nulls_last=True))
            elif field_ordered == "-" + self.SORT_CREATE_DATE:
                order_bys.append(F(field).asc(nulls_first=True))
            else:
                order_bys.append(field_ordered)

        return qs.order_by(*order_bys)


class OrganizationListFilterSet(FilterSet):

    """Filter and sorting for organization listing page."""

    slug = CharFilter(field_name="slug", widget=HiddenInput)

    sort = OrganizationSortOrderingFilter(
        field_name="sort",
        label=_("Sort by"),
    )
