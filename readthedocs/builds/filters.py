from django.utils.translation import ugettext_lazy as _

import django_filters

from builds import constants
from builds.models import Build, Version


ANY_REPO = (
    ('', _('Any')),
)

BUILD_TYPES = ANY_REPO + constants.BUILD_TYPES


class VersionSlugFilter(django_filters.FilterSet):

    class Meta:
        model = Version
        fields = {
            'identifier': ['icontains'],
            'slug': ['icontains'],
        }


class VersionFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(name='project__slug')
    # Allow filtering on slug= or version=
    slug = django_filters.CharFilter(label=_("Name"), name='slug',
                                     lookup_type='exact')
    version = django_filters.CharFilter(label=_("Version"), name='slug',
                                        lookup_type='exact')

    class Meta:
        model = Version
        fields = ['project', 'slug', 'version']


class BuildFilter(django_filters.FilterSet):
    date = django_filters.DateRangeFilter(label=_("Build Date"), name="date", lookup_type='range')
    type = django_filters.ChoiceFilter(label=_("Build Type"),
                                       choices=BUILD_TYPES)

    class Meta:
        model = Build
        fields = ['type', 'date', 'success']
