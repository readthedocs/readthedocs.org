"""
Search Queries
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.projects.querysets import RelatedProjectQuerySet


class SearchQuery(TimeStampedModel):

    """
    Information about the search queries.
    """

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
