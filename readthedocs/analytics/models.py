"""Analytics modeling to help understand the projects on Read the Docs."""

import datetime
from collections import namedtuple
from urllib.parse import urlparse

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project


def _last_30_days_iter():
    """Returns iterator for previous 30 days (including today)."""
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)

    # this includes the current day, len() = 31
    return (thirty_days_ago + timezone.timedelta(days=n) for n in range(31))


class PageViewManager(models.Manager):
    """Manager for PageView model."""

    def register_page_view(self, project, version, filename, path, status):
        """Track page view with the given parameters."""
        # TODO: remove after the migration of duplicate records has been completed.
        if project.has_feature(Feature.DISABLE_PAGEVIEWS):
            return

        # Normalize paths to avoid duplicates.
        filename = "/" + filename.lstrip("/")
        path = "/" + path.lstrip("/")

        page_view, created = self.get_or_create(
            project=project,
            version=version,
            path=filename,
            date=timezone.now().date(),
            status=status,
            defaults={
                "view_count": 1,
                "full_path": path,
            },
        )
        if not created:
            page_view.view_count = models.F("view_count") + 1
            page_view.save(update_fields=["view_count"])
        return page_view


class PageView(models.Model):
    """PageView counts per day for a project, version, and path."""

    project = models.ForeignKey(
        Project,
        related_name="page_views",
        on_delete=models.CASCADE,
    )
    # NOTE: this could potentially be removed,
    # since isn't being used and not all page
    # views (404s) are attached to a version.
    version = models.ForeignKey(
        Version,
        verbose_name=_("Version"),
        related_name="page_views",
        on_delete=models.CASCADE,
        null=True,
    )
    path = models.CharField(
        max_length=4096,
        help_text=_("Path relative to the version."),
    )
    full_path = models.CharField(
        max_length=4096,
        help_text=_("Full path including the version and language parts."),
        null=True,
        blank=True,
    )
    view_count = models.PositiveIntegerField(default=0)
    date = models.DateField(default=datetime.date.today, db_index=True)
    status = models.PositiveIntegerField(
        default=200,
        help_text=_("HTTP status code"),
    )

    objects = PageViewManager()

    class Meta:
        unique_together = ("project", "version", "path", "date", "status")
        # Make sure we have only one record with ``version=None``.
        # https://stackoverflow.com/questions/33307892/django-unique-together-with-nullable-foreignkey.
        constraints = [
            models.UniqueConstraint(
                fields=("project", "path", "date", "status"),
                condition=models.Q(version=None),
                name="analytics_pageview_constraint_unique_without_optional",
            ),
        ]

    @classmethod
    def top_viewed_pages(cls, project, since=None, limit=10, status=200, per_version=False):
        """
        Returns top pages according to view counts.

        :param per_version: If `True`, group the results per version.

        :returns: A list of named tuples ordered by the number of views.
         Each tuple contains: path, url, and count.
        """
        # pylint: disable=too-many-locals
        if since is None:
            since = timezone.now().date() - timezone.timedelta(days=30)

        group_by = "full_path" if per_version else "path"
        queryset = (
            cls.objects.filter(project=project, date__gte=since, status=status)
            .values_list(group_by)
            .annotate(count=Sum("view_count"))
            .values_list(group_by, "count", named=True)
            .order_by("-count")[:limit]
        )

        PageViewResult = namedtuple("PageViewResult", "path, url, count")
        resolver = Resolver()
        result = []
        parsed_domain = urlparse(resolver.get_domain(project))
        default_version = project.get_default_version()
        for row in queryset:
            if not per_version:
                # If we aren't groupig by version,
                # then always link to the default version.
                url_path = resolver.resolve_path(
                    project=project,
                    version_slug=default_version,
                    filename=row.path,
                )
            else:
                url_path = row.full_path or ""
            url = parsed_domain._replace(path=url_path).geturl()
            path = row.full_path if per_version else row.path
            result.append(
                PageViewResult(
                    path=path,
                    url=url,
                    count=row.count,
                )
            )
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

        count_dict = dict(queryset.order_by("date").values_list("date", "total_views"))

        # This fills in any dates where there is no data
        # to make sure we have a full 30 days of dates
        count_data = [count_dict.get(date) or 0 for date in _last_30_days_iter()]

        # format the date value to a more readable form
        # Eg. `16 Jul`
        last_30_days_str = [
            timezone.datetime.strftime(date, "%d %b") for date in _last_30_days_iter()
        ]

        final_data = {
            "labels": last_30_days_str,
            "int_data": count_data,
        }

        return final_data
