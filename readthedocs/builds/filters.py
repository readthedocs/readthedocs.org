import django_filters

from builds import constants
from builds.models import Build, Version


ANY_REPO = (
    ('', 'Any'),
)

BUILD_TYPES = ANY_REPO + constants.BUILD_TYPES


class VersionFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(name='project__name', lookup_type="icontains")
    slug= django_filters.CharFilter(label="Slug", name='slug', lookup_type='icontains')

    class Meta:
        model = Version
        fields = ['project', 'slug']

class BuildFilter(django_filters.FilterSet):
    date = django_filters.DateRangeFilter(label="Build Date", name="date")
    type = django_filters.ChoiceFilter(label="Build Type", choices=BUILD_TYPES)

    class Meta:
        model = Build
        fields = ['type', 'date', 'version', 'success']

