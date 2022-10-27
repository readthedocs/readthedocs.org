from django.core.management.base import BaseCommand

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.models import SearchQuery


class Command(BaseCommand):

    help = __doc__

    def load_data(self):
        project = Project.objects.get(slug="pip")
        version = Version.objects.get(project_id=project.id, slug="0.8")
        for pk, query, created, modified in [
            (5, "search", "2019-08-02T00:00:00Z", "2019-08-02T00:00:00Z"),
            (6, "sphinx", "2019-08-02T00:20:00Z", "2019-08-02T00:20:00Z"),
            (7, "read the docs", "2019-08-02T01:30:00Z", "2019-08-02T01:30:00Z"),
            (8, "elasticsearch", "2019-08-02T02:00:00Z", "2019-08-02T02:00:00Z"),
            (9, "hello", "2019-08-02T03:00:00Z", "2019-08-02T03:00:00Z"),
            (10, "advertising", "2019-08-02T05:00:00Z", "2019-08-02T05:00:00Z"),
            (11, "github", "2019-08-02T04:00:00Z", "2019-08-02T04:00:00Z"),
            (12, "advertising", "2019-08-01T15:00:00Z", "2019-08-01T15:00:00Z"),
            (13, "advertising", "2019-08-01T15:15:00Z", "2019-08-01T15:15:00Z"),
            (14, "sphinx", "2019-08-01T16:00:00Z", "2019-08-01T16:00:00Z"),
            (15, "read the docs", "2019-07-31T20:00:00Z", "2019-07-31T20:00:00Z"),
            (16, "read the docs", "2019-07-31T20:20:00Z", "2019-07-31T20:20:00Z"),
            (17, "read the docs", "2019-07-31T20:30:00Z", "2019-07-31T20:30:00Z"),
            (18, "elasticsearch", "2019-07-31T21:00:00Z", "2019-07-31T21:00:00Z"),
            (19, "documentation", "2019-07-15T06:00:00Z", "2019-07-15T06:00:00Z"),
            (20, "documentation", "2019-07-16T12:00:00Z", "2019-07-16T12:00:00Z"),
            (21, "documentation", "2019-07-17T18:00:00Z", "2019-07-17T18:00:00Z"),
            (22, "documentation", "2019-07-17T12:00:00Z", "2019-07-17T12:00:00Z"),
            (23, "hello world", "2019-06-10T06:00:00Z", "2019-06-10T06:00:00Z"),
            (24, "hello world", "2019-06-11T18:00:00Z", "2019-06-11T18:00:00Z"),
            (25, "hello world", "2019-06-12T18:00:00Z", "2019-06-12T18:00:00Z"),
            (26, "hello world", "2019-07-02T18:00:00Z", "2019-07-02T18:00:00Z"),
            (27, "hello world", "2019-06-25T18:00:00Z", "2019-06-25T18:00:00Z"),
        ]:
            SearchQuery.objects.get_or_create(
                id=pk,
                project=project,
                version=version,
                query=query,
                created=created,
                modified=modified,
            )

    def handle(self, *args, **kwargs):
        self.load_data()
        self.stdout.write("Loaded search queries data")
