import django_filters.rest_framework as filters
from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project


class ProjectFilter(filters.FilterSet):
    name__contains = filters.CharFilter(field_name='name', lookup_expr='contains')
    slug__contains = filters.CharFilter(field_name='slug', lookup_expr='contains')
    repository_type = filters.CharFilter(field_name='repo_type', lookup_expr='exact')

    class Meta:
        model = Project
        fields = [
            'name',
            'name__contains',
            'slug',
            'slug__contains',
            'language',
            'privacy_level',
            'programming_language',
            'repository_type',
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


class BuildFilter(filters.FilterSet):
    running = filters.BooleanFilter(method='get_running')

    class Meta:
        model = Build
        fields = [
            'commit',
            'running',
        ]

    def get_running(self, queryset, name, value):
        if value:
            return queryset.exclude(state=BUILD_STATE_FINISHED)
        else:
            return queryset.filter(state=BUILD_STATE_FINISHED)
