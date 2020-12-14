"""Analytics modeling to help understand the projects on Read the Docs."""

import datetime

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


def _last_30_days_iter():
    """Returns iterator for previous 30 days (including today)."""
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)

    # this includes the current day, len() = 31
    return (thirty_days_ago + timezone.timedelta(days=n) for n in range(31))


class PageView(models.Model):

    """PageView counts per day for a project, version, and path."""

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
    view_count = models.PositiveIntegerField(default=0)
    date = models.DateField(default=datetime.date.today, db_index=True)

    class Meta:
        unique_together = ("project", "version", "path", "date")

    def __str__(self):
        return f'PageView: [{self.project.slug}:{self.version.slug}] - {self.path} for {self.date}'

    @classmethod
    def top_viewed_pages(cls, project, since=None):
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
        if since is None:
            since = timezone.now().date() - timezone.timedelta(days=30)

        queryset = (
            cls.objects
            .filter(project=project, date__gte=since)
            .values_list('path')
            .annotate(total_views=Sum('view_count'))
            .values_list('path', 'total_views')
            .order_by('-total_views')[:10]
        )

        pages = []
        view_counts = []

        for data in queryset.iterator():
            pages.append(data[0])
            view_counts.append(data[1])

        final_data = {
            'pages': pages,
            'view_counts': view_counts,
        }

        return final_data

    @classmethod
    def page_views_by_date(cls, project_slug, since=None):
        """
        Returns the total page views count for last 30 days for a particular project.

        Structure of returned data is compatible to make graphs.
        Sample returned data::
            {
                'labels': ['01 Jul', '02 Jul', '03 Jul'],
                'int_data': [150, 200, 143]
            }
        This data shows that there were 150 page views on 01 July,
        200 page views on 02 July and 143 page views on 03 July.
        """
        if since is None:
            since = timezone.now().date() - timezone.timedelta(days=30)

        queryset = cls.objects.filter(
            project__slug=project_slug,
            date__gte=since,
        ).values('date').annotate(total_views=Sum('view_count')).order_by('date')

        count_dict = dict(
            queryset.order_by('date').values_list('date', 'total_views')
        )

        # This fills in any dates where there is no data
        # to make sure we have a full 30 days of dates
        count_data = [count_dict.get(date) or 0 for date in _last_30_days_iter()]

        # format the date value to a more readable form
        # Eg. `16 Jul`
        last_30_days_str = [
            timezone.datetime.strftime(date, '%d %b')
            for date in _last_30_days_iter()
        ]

        final_data = {
            'labels': last_30_days_str,
            'int_data': count_data,
        }

        return final_data
