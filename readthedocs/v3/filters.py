import django_filters.rest_framework as filters
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
