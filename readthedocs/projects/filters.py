import django_filters

from projects import constants
from projects.models import Project

ANY_REPO = (
    ('', 'Any'),
)

REPO_CHOICES = ANY_REPO + constants.REPO_CHOICES

class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label="Name", name='name', lookup_type='icontains')
    pub_date = django_filters.DateRangeFilter(label="Created Date", name="pub_date")
    repo = django_filters.CharFilter(label="Repository URL", name='repo', lookup_type='icontains')
    repo_type = django_filters.ChoiceFilter(
        label="Repository",
        name='repo',
        lookup_type='icontains',
        choices=REPO_CHOICES,
    )

    class Meta:
        model = Project
        fields = ['name', 'pub_date', 'repo', 'repo_type']
