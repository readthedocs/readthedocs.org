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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra['choices'] = [
            ('name', _('Name')),
            ('-name', _('Name (descending)')),
            ('-recent', _('Most recently built')),
            ('recent', _('Least recently built')),
        ]

    def filter(self, qs, value):
        # This is where we use the None value for this custom filter. This
        # doesn't work with a standard model filter. Note: ``value`` is always
        # an iterable, but can be empty.
        if not value:
            value = ['relevance']

        # Selectively add anotations as a small query optimization
        annotations = {
            # Default ordering is number of builds, but could be another proxy
            # for version populatrity
            'relevance': {'relevance': Count('builds')},
            # Most recent build date, this appears inverted in the option value
            'recent': {'recent': Max('builds__date')},
            # Alias field name here, as ``OrderingFilter`` was having trouble
            # doing this with it's native field mapping
            'name': {'name': F('verbose_name')},
        }
        # And copy the negative sort lookups, ``value`` might be ``['-recent']``
        annotations.update({f'-{key}': value for (key, value) in annotations.items()})

        annotation = annotations.get(*value)
        return qs.annotate(**annotation).order_by(*value)


class ProjectSortOrderingFilter(OrderingFilter):

    """
    Project list sort ordering django_filters filter.

    Django-filter is highly opionated, and the default model filters do not work
    well with empty/null values in the filter choices. In our case, empty/null
    values are used for a default query. So, to make this work, we will use a
    custom filter, instead of an automated model filter.
    """

    SORT_NAME = 'name'
    SORT_MODIFIED_DATE = 'modified_date'
    SORT_BUILD_DATE = 'built_last'
    SORT_BUILD_COUNT = 'build_count'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra['choices'] = [
            (f'-{self.SORT_NAME}', _('Name (descending)')),
            (f'-{self.SORT_MODIFIED_DATE}', _('Most recently modified')),
            (self.SORT_MODIFIED_DATE, _('Least recently modified')),
            (self.SORT_BUILD_DATE, _('Most recently built')),
            (f'-{self.SORT_BUILD_DATE}', _('Least recently built')),
            (f'-{self.SORT_BUILD_COUNT}', _('Most frequently built')),
            (self.SORT_BUILD_COUNT, _('Least frequently built')),
        ]

    def filter(self, qs, value):
        # This is where we use the None value from the custom filter
        if value is None:
            value = [self.SORT_NAME]
        return qs.annotate(
            **{
                self.SORT_BUILD_DATE: Max('versions__builds__date'),
                self.SORT_BUILD_COUNT: Count('versions__builds'),
            }
        ).order_by(*value)


class ProjectListFilterSet(FilterSet):

    """
    Project list filter set for project list view.

    This filter set enables list view sorting using a custom filter, and
    provides search-as-you-type lookup filter as well.
    """

    project = CharFilter(field_name='slug', widget=HiddenInput)
    sort = ProjectSortOrderingFilter(
        field_name='sort',
        label=_('Sort by'),
        empty_label=_('Name'),
    )


class ProjectVersionListFilterSet(FilterSet):

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

    sort = VersionSortOrderingFilter(
        field_name='sort',
        label=_('Sort by'),
        empty_label=_('Relevance'),
    )

    def get_visibility(self, queryset, name, value):
        if value == self.VISIBILITY_HIDDEN:
            return queryset.filter(hidden=True)
        if value == self.VISIBILITY_VISIBLE:
            return queryset.filter(hidden=False)
        return queryset
