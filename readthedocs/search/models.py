"""Search Queries."""

from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncDate
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
    objects = RelatedProjectQuerySet.as_manager()

    class Meta:
        verbose_name = 'Search query'
        verbose_name_plural = 'Search queries'

    def __str__(self):
        return f'[{self.project.slug}:{self.version.slug}]: {self.query}'

    @classmethod
    def generate_queries_count_of_one_month(cls, project_slug):
        """
        Returns the total queries performed each day of the last 30 days (including today).

        Structure of returned data is compatible to make graphs.
        Sample returned data::
            {
                'labels': ['01 Jul', '02 Jul', '03 Jul'],
                'int_data': [150, 200, 143]
            }
        This data shows that there were 150 searches were made on 01 July,
        200 searches on 02 July and 143 searches on 03 July.
        """
        today = timezone.now().date()
        last_30th_day = timezone.now().date() - timezone.timedelta(days=30)

        # this includes the current day also
        last_31_days_iter = [last_30th_day + timezone.timedelta(days=n) for n in range(31)]

        qs = cls.objects.filter(
            project__slug=project_slug,
            created__date__lte=today,
            created__date__gte=last_30th_day,
        ).order_by('-created')

        # dict containing the total number of queries
        # of each day for the past 30 days (if present in database).
        count_dict = dict(
            qs.annotate(created_date=TruncDate('created'))
            .values('created_date')
            .order_by('created_date')
            .annotate(count=Count('id'))
            .values_list('created_date', 'count')
        )

        count_data = [count_dict.get(date) or 0 for date in last_31_days_iter]

        # format the date value to a more readable form
        # Eg. `16 Jul`
        last_31_days_str = [
            timezone.datetime.strftime(date, '%d %b')
            for date in last_31_days_iter
        ]

        final_data = {
            'labels': last_31_days_str,
            'int_data': count_data,
        }

        return final_data
