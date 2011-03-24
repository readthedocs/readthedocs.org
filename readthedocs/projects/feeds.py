from django.contrib.syndication.views import Feed
from django.db.models import Max

from projects.models import Project

class LatestProjectsFeed(Feed):
    title = "Recently updated documentation"
    link = "http://readthedocs.org"
    description = "Recently updated documentation on Read the Docs"

    def items(self):
        return Project.objects.filter(builds__isnull=False).annotate(max_date=Max('builds__date')).order_by('-max_date')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

class NewProjectsFeed(Feed):
    title = "Newest documentation"
    link = "http://readthedocs.org"
    description = "Recently created documentation on Read the Docs"

    def items(self):
        return Project.objects.all().order_by('-pk')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description
