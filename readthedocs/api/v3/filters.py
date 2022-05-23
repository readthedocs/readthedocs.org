import django_filters.rest_framework as filters

from readthedocs.builds.constants import BUILD_FINAL_STATES
from readthedocs.builds.models import Build, Version
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.projects.models import Project


class ProjectFilter(filters.FilterSet):

    class Meta:
        model = Project
        fields = [
            'language',
            'programming_language',
        ]


class VersionFilter(filters.FilterSet):
    slug = filters.CharFilter(lookup_expr='icontains')
    verbose_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Version
        fields = [
            'verbose_name',
            'privacy_level',
            'active',
            'built',
            'uploaded',
            'slug',
            'type',
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
            return queryset.exclude(state__in=BUILD_FINAL_STATES)

        return queryset.filter(state__in=BUILD_FINAL_STATES)


class RemoteRepositoryFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    organization = filters.CharFilter(field_name='organization__slug')

    class Meta:
        model = RemoteRepository
        fields = [
            'name',
            'vcs_provider',
            'organization',
        ]


class RemoteOrganizationFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = RemoteOrganization
        fields = [
            'name',
            'vcs_provider',
        ]
