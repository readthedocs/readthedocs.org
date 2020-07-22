import django_filters.rest_framework as filters

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project


class ProjectFilter(filters.FilterSet):

    class Meta:
        model = Project
        fields = [
            'language',
            'programming_language',
        ]


class VersionFilter(filters.FilterSet):

    class Meta:
        model = Version
        fields = [
            'verbose_name',
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

        return queryset.filter(state=BUILD_STATE_FINISHED)
