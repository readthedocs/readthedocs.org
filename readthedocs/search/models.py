"""Search Queries."""

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.querysets import RelatedProjectQuerySet


class SearchQuery(TimeStampedModel):

    """Information about the search queries."""

    project = models.ForeignKey(
        Project,
        related_name='search_queries',
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        Version,
        verbose_name=_('Version'),
        related_name='search_queries',
        on_delete=models.CASCADE,
    )
    query = models.CharField(
        _('Query'),
        max_length=4092,
    )
    count = models.PositiveIntegerField(
        _('No. of times this query was searched'),
        default=1,
    )
    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        verbose_name = 'Search query'
        verbose_name_plural = 'Search queries'

    def __str__(self):
        return f'[{self.project.slug}:{self.version.slug}]: {self.query}'

    @classmethod
    def generate_line_chart_data(cls, project_slug, version_slug):
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        last_30th_day = timezone.now().date() - timezone.timedelta(days=30)
        last_30_days_iter = [last_30th_day + timezone.timedelta(days=n) for n in range(30)]

        qs = cls.objects.filter(
            project__slug=project_slug,
            version__slug=version_slug,
            modified__date__lte=yesterday,
            modified__date__gte=last_30th_day,
        ).order_by('-modified')

        count_data = [
            qs.filter(modified__date=date).count()
            for date in last_30_days_iter
        ]

        # format the date string to more readable form
        # Eg. `16 Jul`
        last_30_days_str = [
            timezone.datetime.strftime(date, '%d %b')
            for date in last_30_days_iter
        ]

        final_data = {
            'labels': last_30_days_str,
            'int_data': count_data,
        }

        return final_data
