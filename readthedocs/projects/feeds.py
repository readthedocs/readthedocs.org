"""Project RSS feeds"""

from __future__ import absolute_import
from django.contrib.syndication.views import Feed

from readthedocs.projects.models import Project


class LatestProjectsFeed(Feed):

    """RSS feed for projects that were recently updated"""

    title = "Recently updated documentation"
    link = "http://readthedocs.org"
    description = "Recently updated documentation on Read the Docs"

    def items(self):
        return Project.objects.public().order_by('-modified_date')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.get_latest_build()


class NewProjectsFeed(Feed):

    """RSS feed for newly created projects"""

    title = "Newest documentation"
    link = "http://readthedocs.org"
    description = "Recently created documentation on Read the Docs"

    def items(self):
        return Project.objects.public().order_by('-pk')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.get_latest_build()
