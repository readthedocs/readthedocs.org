"""Utility functions used by projects."""

import logging
import os
from collections import OrderedDict

from django.conf import settings
from django.db.models import Count


log = logging.getLogger(__name__)


# TODO make this a classmethod of Version
def version_from_slug(slug, version):
    from readthedocs.builds.models import Version, APIVersion
    from readthedocs.api.v2.client import api
    if settings.DONT_HIT_DB:
        version_data = api.version().get(
            project=slug,
            slug=version,
        )['results'][0]
        v = APIVersion(**version_data)
    else:
        v = Version.objects.get(project__slug=slug, slug=version)
    return v


def safe_write(filename, contents):
    """
    Normalize and write to filename.

    Write ``contents`` to the given ``filename``. If the filename's
    directory does not exist, it is created. Contents are written as UTF-8,
    ignoring any characters that cannot be encoded as UTF-8.

    :param filename: Filename to write to
    :param contents: File contents to write to file
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename, 'w', encoding='utf-8', errors='ignore') as fh:
        fh.write(contents)
        fh.close()


def _get_search_queries_from_queryset(queryset, sort=True):
    """
    Return list of search queries from queryset.

    If ``sort`` is True, resulted list will be ordered in the descending order,
    from most searched query to least search query.
    Sample returned data: ['query1', 'query2', 'query3']
    :param queryset: Queryset of the class SearchQuery
    :type queryset: projects.querysets.RelatedProjectQuerySetBase
    :param sort: If set to true, result will be sorted in descending order of most searched query
    :type sort: bool
    :returns: list of search queries
    :rtype: list
    """
    count_data =  (
        queryset.values('query')
        .annotate(count=Count('id'))
    )

    if sort:
        # If sort is true, order the results by ``count``.
        count_data = count_data.order_by('-count')

    final_values = count_data.values_list('query', flat=True)

    # This is done to prevent duplication of queries in the result.
    final_values = list(OrderedDict.fromkeys(final_values))
    return final_values
