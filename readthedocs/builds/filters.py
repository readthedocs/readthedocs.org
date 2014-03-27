from django.utils.translation import ugettext_lazy as _

import django_filters

from builds import constants
from builds.models import Build, Version


ANY_REPO = (
    ('', _('Any')),
)

BUILD_TYPES = ANY_REPO + constants.BUILD_TYPES


class VersionSlugFilter(django_filters.FilterSet):
    slug = django_filters.CharFilter(label=_("Name"), name='slug',
                                     lookup_type='icontains')
    tag = django_filters.CharFilter(label=_("Tag"), name='tags',
                                    lookup_type='name__icontains')

    class Meta:
        model = Version
        fields = ['slug', 'tag']


class VersionFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(name='project__slug')
    slug = django_filters.CharFilter(label=_("Name"), name='slug',
                                     lookup_type='icontains')

    class Meta:
        model = Version
        fields = ['project', 'slug']


class BuildFilter(django_filters.FilterSet):
    date = django_filters.DateRangeFilter(label=_("Build Date"), name="date")
    type = django_filters.ChoiceFilter(label=_("Build Type"),
                                       choices=BUILD_TYPES)

    class Meta:
        model = Build
        fields = ['type', 'date', 'success']
