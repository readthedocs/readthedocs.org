from django.utils.translation import ugettext_lazy as _

import django_filters

from projects import constants
from projects.models import Project

ANY_REPO = (
    ('', _('Any')),
)

REPO_CHOICES = ANY_REPO + constants.REPO_CHOICES


class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Name"), name='name',
                                     lookup_type='icontains')
    slug = django_filters.CharFilter(label=_("Slug"), name='slug',
                                     lookup_type='icontains')
    pub_date = django_filters.DateRangeFilter(label=_("Created Date"),
                                              name="pub_date")
    repo = django_filters.CharFilter(label=_("Repository URL"), name='repo',
                                     lookup_type='icontains')
    repo_type = django_filters.ChoiceFilter(
        label=_("Repository Type"),
        name='repo',
        lookup_type='icontains',
        choices=REPO_CHOICES,
    )

    class Meta:
        model = Project
        fields = ['name', 'slug', 'pub_date', 'repo', 'repo_type']
