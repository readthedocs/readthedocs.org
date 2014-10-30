from django.utils.translation import ugettext_lazy as _

import django_filters

from projects import constants
from projects.models import Project

ANY_REPO = (
    ('', _('Any')),
)

REPO_CHOICES = ANY_REPO + constants.REPO_CHOICES


def sort_slug(queryset, query):
    queryset = queryset.filter(slug__icontains=query)
    ret = []
    ret.extend([q.pk for q in queryset if q.slug == query])
    ret.extend([q.pk for q in queryset if q.slug.startswith(query) and q.pk not in ret])
    ret.extend([q.pk for q in queryset if q.slug.endswith(query) and q.pk not in ret])
    ret.extend([q.pk for q in queryset if q.pk not in ret])

    # Create a QS preserving ordering
    # http://blog.mathieu-leplatre.info/django-create-a-queryset-from-a-list-preserving-order.html
    clauses = ' '.join(['WHEN projects_project.id=%s THEN %s' % (pk, i) for i, pk in enumerate(ret)])
    ordering = 'CASE %s END' % clauses
    ret_queryset = Project.objects.filter(pk__in=ret).extra(
        select={'ordering': ordering}, order_by=('ordering',))
    return ret_queryset


class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label=_("Name"), name='name',
                                     lookup_type='icontains')
    slug = django_filters.CharFilter(label=_("Slug"), name='slug', action=sort_slug)
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
