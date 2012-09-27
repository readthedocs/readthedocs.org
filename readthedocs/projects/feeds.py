from django.contrib.syndication.views import Feed
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

from projects.models import Project

class LatestProjectsFeed(Feed):
    title = _("Recently updated documentation")
    link = "http://readthedocs.org"
    description = _("Recently updated documentation on Read the Docs")

    def items(self):
        return Project.objects.order_by('-modified_date')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.get_latest_build()

class NewProjectsFeed(Feed):
    title = _("Newest documentation")
    link = "http://readthedocs.org"
    description = _("Recently created documentation on Read the Docs")

    def items(self):
        return Project.objects.all().order_by('-pk')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.get_latest_build()
