"""Search Queries."""

from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.querysets import RelatedProjectQuerySet
from readthedocs.search.utils import _get_last_31_days_iter, _get_last_31_days_str


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
        last_31_days_iter = _get_last_31_days_iter()

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
        last_31_days_str = _get_last_31_days_str(date_format='%d %b')

        final_data = {
            'labels': last_31_days_str,
            'int_data': count_data,
        }

        return final_data


class PageView(models.Model):
    project = models.ForeignKey(
        Project,
        related_name='page_views',
        on_delete=models.CASCADE,
    )
    version = models.ForeignKey(
        Version,
        verbose_name=_('Version'),
        related_name='page_views',
        on_delete=models.CASCADE,
    )
    path = models.CharField(max_length=4096)
    view_count = models.PositiveIntegerField(default=1)
    date = models.DateField()

    def __str__(self):
        return f'[{self.project.slug}:{self.version.slug}]: {self.path}'

    @classmethod
    def get_top_viewed_pages(cls, project):
        """
        Returns top 10 pages according to view counts.

        Structure of returned data is compatible to make graphs.
        Sample returned data::
        {
            'pages': ['index', 'config-file/v1', 'intro/import-guide'],
            'view_counts': [150, 120, 100]
        }
        This data shows that `index` is the most viewed page having 150 total views,
        followed by `config-file/v1` and `intro/import-guide` having 120 and
        100 total page views respectively.
        """
        qs = (
            cls.objects
            .filter(project=project)
            .values_list('path')
            .annotate(total_views=Sum('view_count'))
            .values_list('path', 'total_views')
            .order_by('-total_views')[:10]
        )

        pages = []
        view_counts = []

        for data in qs.iterator():
            pages.append(data[0])
            view_counts.append(data[1])

        final_data = {
            'pages': pages,
            'view_counts': view_counts,
        }

        return final_data

    @classmethod
    def get_page_view_count_of_one_month(cls, project_slug, page_path):
        """
        Returns the total page views count for last 30 days for a particular `page_path`.

        Structure of returned data is compatible to make graphs.
        Sample returned data::
            {
                'labels': ['01 Jul', '02 Jul', '03 Jul'],
                'int_data': [150, 200, 143]
            }
        This data shows that there were 150 page views on 01 July,
        200 page views on 02 July and 143 page views on 03 July for a particular `page_path`.
        """
        today = timezone.now().date()
        last_30th_day = timezone.now().date() - timezone.timedelta(days=30)

        # this includes the current day also
        last_31_days_iter = _get_last_31_days_iter()

        qs = cls.objects.filter(
            project__slug=project_slug,
            path=page_path,
        ).order_by('-date')

        count_dict = dict(
            qs.values('date')
            .order_by('date')
            .values_list('date', 'view_count')
        )

        count_data = [count_dict.get(date) or 0 for date in last_31_days_iter]

        # format the date value to a more readable form
        # Eg. `16 Jul`
        last_31_days_str = _get_last_31_days_str(date_format='%d %b')

        final_data = {
            'labels': last_31_days_str,
            'int_data': count_data,
        }

        return final_data
