import django_filters.rest_framework as filters
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class ProjectFilter(filters.FilterSet):
    name__contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    slug__contains = filters.CharFilter(field_name='slug', lookup_expr='contains')

    class Meta:
        model = Project
        fields = [
            'name',
            'name__contains',
            'slug',
            'slug__contains',
            'privacy_level',
        ]


class VersionFilter(filters.FilterSet):
    verbose_name__contains = filters.CharFilter(
        field_name='versbose_name',
        lookup_expr='contains',
    )
    slug__contains = filters.CharFilter(field_name='slug', lookup_expr='contains')

    class Meta:
        model = Version
        fields = [
            'verbose_name',
            'verbose_name__contains',
            'slug',
            'slug__contains',
            'privacy_level',
            'active',
            'built',
            'uploaded',
        ]
