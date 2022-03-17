"""Analytics modeling to help understand the projects on Read the Docs."""
import datetime
from collections import namedtuple
from urllib.parse import urlparse

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.core.resolver import resolve, resolve_path
from readthedocs.projects.models import Project


def _last_30_days_iter():
    """Returns iterator for previous 30 days (including today)."""
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)

    # this includes the current day, len() = 31
    return (thirty_days_ago + timezone.timedelta(days=n) for n in range(31))


class PageViewManager(models.Manager):
    def register_page_view(self, project, version, path, status):
        # Normalize path to avoid duplicates.
        path = path.strip('/')
        if not path:
            path = '/'
        fields = dict(
            project=project,
            version=version,
            path=path,
            date=timezone.now().date(),
            status=status,
        )
        page_view, created = self.get_or_create(
            **fields,
            defaults={"view_count": 1},
        )
        if not created:
            page_view.view_count = models.F("view_count") + 1
            page_view.save(update_fields=["view_count"])
        return page_view


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
        null=True,
    )
    path = models.CharField(max_length=4096)
    view_count = models.PositiveIntegerField(default=0)
    date = models.DateField(default=datetime.date.today, db_index=True)
    status = models.PositiveIntegerField(
        default=200,
        help_text=_("HTTP status code"),
    )

    objects = PageViewManager()

    class Meta:
        unique_together = ("project", "version", "path", "date", "status")

    def __str__(self):
        return f'PageView: [{self.project.slug}:{self.version.slug}] - {self.path} for {self.date}'

    @classmethod
    def top_viewed_pages(cls, project, since=None, limit=10, status=200, per_version=False):
        """
        Returns top pages according to view counts.

        :param per_version: If `True`, group the results per version.

        :returns: A list of named tuples ordered by the number of views.
         Each tuple contains: path, full_path, and total_views.
        """
        if since is None:
            since = timezone.now().date() - timezone.timedelta(days=30)

        group_by = ["path"]
        values = ["path", "total_views"]
        if per_version:
            group_by.append("version")
            values.append("version__slug")

        queryset = (
            cls.objects.filter(project=project, date__gte=since, status=status)
            .values_list(*group_by)
            .annotate(total_views=Sum("view_count"))
            .values_list(*values, named=True)
            .order_by("-total_views")[:limit]
        )

        PageViewResult = namedtuple('PageViewResult', 'path, full_path, count')
        result = []
        parsed_domain = urlparse(resolve(project))
        default_version = project.get_default_version()
        for row in queryset:
            version_slug = default_version
            if per_version:
                version_slug = row.version__slug

            if version_slug:
                path = resolve_path(
                    project=project,
                    version_slug=version_slug,
                    filename=row.path,
                )
            else:
                # If there isn't a version,
                # then the path starts at the root of the domain.
                path = row.path
            full_path = parsed_domain._replace(path=path).geturl()
            result.append(PageViewResult(
                path=path if per_version else row.path,
                full_path=full_path,
                count=row.total_views,
            ))
        return result

    @classmethod
    def page_views_by_date(cls, project_slug, since=None, status=200):
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

        queryset = (
            cls.objects.filter(
                project__slug=project_slug,
                date__gte=since,
                status=status,
            )
            .values("date")
            .annotate(total_views=Sum("view_count"))
            .order_by("date")
        )

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
