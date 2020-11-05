import logging

from django.db.models import Count, F, Max
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from django_filters import CharFilter, ChoiceFilter, FilterSet, OrderingFilter

log = logging.getLogger(__name__)


class SortOrderingFilter(OrderingFilter):

    """
    Special sort filter for non-model field ordering.

    Django-filter is highly opionated and this filter is very difficult to use,
    especially when using empty/null values in the filter choices. In our case,
    empty/null values are used for a default query, which is impossible to do
    without a custom ``Filter`` because ``Filter`` doesn't alter the queryset if
    the field value looks like it is empty/null.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra['choices'] = [
            ('name', _('Name')),
            ('-name', _('Name (descending)')),
            ('-recent', _('Most recently built')),
            ('recent', _('Least recently built')),
        ]

    def filter(self, queryset, values):
        if values is None:
            values = ['relevance']
        return queryset.annotate(
            # Default ordering is number of builds, but could be another proxy
            # for version populatrity
            relevance=Count('builds'),
            # Most recent build date, this appears inverted in the option value
            recent=Max('builds__date'),
            # Alias field name here, as ``OrderingFilter`` was having trouble
            # doing this with it's native field mapping
            name=F('verbose_name'),
        ).order_by(*values)


class ProjectVersionSearchFilter(FilterSet):

    """
    Filter and sorting for project version listing page.

    This is used from the project versions list view page to provide filtering
    and sorting to the version list and search UI. It is normally instantiated
    with an included queryset, which provides user project authorization.
    """

    VISIBILITY_HIDDEN = 'hidden'
    VISIBILITY_VISIBLE = 'visible'

    VISIBILITY_CHOICES = (
        ('hidden', _('Hidden versions')),
        ('visible', _('Visible versions')),
    )

    PRIVACY_CHOICES = (
        ('public', _('Public versions')),
        ('private', _('Private versions')),
    )

    # Attribute filter fields
    version = CharFilter(field_name='slug', widget=HiddenInput)
    privacy = ChoiceFilter(
        field_name='privacy_level',
        label=_('Privacy'),
        choices=PRIVACY_CHOICES,
        empty_label=_('Any'),
    )
    # This field looks better as ``visibility=hidden`` than it does
    # ``hidden=true``, otherwise we could use a BooleanFilter instance here
    # instead
    visibility = ChoiceFilter(
        field_name='hidden',
        label=_('Visibility'),
        choices=VISIBILITY_CHOICES,
        method='get_visibility',
        empty_label=_('Any'),
    )

    # For sorting
    sort = SortOrderingFilter(
        field_name='sort',
        label=_('Sort by'),
        empty_label=_('Relevance'),
    )

    def get_visibility(self, queryset, name, value):
        if value == self.VISIBILITY_HIDDEN:
            return queryset.filter(hidden=True)
        elif value == self.VISIBILITY_VISIBLE:
            return queryset.filter(hidden=False)
        return queryset
