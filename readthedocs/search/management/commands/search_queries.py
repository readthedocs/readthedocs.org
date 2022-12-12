import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.models import SearchQuery


class Command(BaseCommand):

    help = __doc__

    def load_data(self):
        project = Project.objects.get(slug="pip")
        version = Version.objects.get(project_id=project.id, slug="0.8")
        queries = [
            {
                "id": 5,
                "project": project,
                "version": version,
                "query": "search",
                "created": "2019-08-02T00:00:00Z",
                "modified": "2019-08-02T00:00:00Z",
            },
            {
                "id": 6,
                "project": project,
                "version": version,
                "query": "sphinx",
                "created": "2019-08-02T00:20:00Z",
                "modified": "2019-08-02T00:20:00Z",
            },
            {
                "id": 7,
                "project": project,
                "version": version,
                "query": "read the docs",
                "created": "2019-08-02T01:30:00Z",
                "modified": "2019-08-02T01:30:00Z",
            },
            {
                "id": 8,
                "project": project,
                "version": version,
                "query": "elasticsearch",
                "created": "2019-08-02T02:00:00Z",
                "modified": "2019-08-02T02:00:00Z",
            },
            {
                "id": 9,
                "project": project,
                "version": version,
                "query": "hello",
                "created": "2019-08-02T03:00:00Z",
                "modified": "2019-08-02T03:00:00Z",
            },
            {
                "id": 10,
                "project": project,
                "version": version,
                "query": "advertising",
                "created": "2019-08-02T05:00:00Z",
                "modified": "2019-08-02T05:00:00Z",
            },
            {
                "id": 11,
                "project": project,
                "version": version,
                "query": "github",
                "created": "2019-08-02T04:00:00Z",
                "modified": "2019-08-02T04:00:00Z",
            },
            {
                "id": 12,
                "project": project,
                "version": version,
                "query": "advertising",
                "created": "2019-08-01T15:00:00Z",
                "modified": "2019-08-01T15:00:00Z",
            },
            {
                "id": 13,
                "project": project,
                "version": version,
                "query": "advertising",
                "created": "2019-08-01T15:15:00Z",
                "modified": "2019-08-01T15:15:00Z",
            },
            {
                "id": 14,
                "project": project,
                "version": version,
                "query": "sphinx",
                "created": "2019-08-01T16:00:00Z",
                "modified": "2019-08-01T16:00:00Z",
            },
            {
                "id": 15,
                "project": project,
                "version": version,
                "query": "read the docs",
                "created": "2019-07-31T20:00:00Z",
                "modified": "2019-07-31T20:00:00Z",
            },
            {
                "id": 16,
                "project": project,
                "version": version,
                "query": "read the docs",
                "created": "2019-07-31T20:20:00Z",
                "modified": "2019-07-31T20:20:00Z",
            },
            {
                "id": 17,
                "project": project,
                "version": version,
                "query": "read the docs",
                "created": "2019-07-31T20:30:00Z",
                "modified": "2019-07-31T20:30:00Z",
            },
            {
                "id": 18,
                "project": project,
                "version": version,
                "query": "elasticsearch",
                "created": "2019-07-31T21:00:00Z",
                "modified": "2019-07-31T21:00:00Z",
            },
            {
                "id": 19,
                "project": project,
                "version": version,
                "query": "documentation",
                "created": "2019-07-15T06:00:00Z",
                "modified": "2019-07-15T06:00:00Z",
            },
            {
                "id": 20,
                "project": project,
                "version": version,
                "query": "documentation",
                "created": "2019-07-16T12:00:00Z",
                "modified": "2019-07-16T12:00:00Z",
            },
            {
                "id": 21,
                "project": project,
                "version": version,
                "query": "documentation",
                "created": "2019-07-17T18:00:00Z",
                "modified": "2019-07-17T18:00:00Z",
            },
            {
                "id": 22,
                "project": project,
                "version": version,
                "query": "documentation",
                "created": "2019-07-17T12:00:00Z",
                "modified": "2019-07-17T12:00:00Z",
            },
            {
                "id": 23,
                "project": project,
                "version": version,
                "query": "hello world",
                "created": "2019-06-10T06:00:00Z",
                "modified": "2019-06-10T06:00:00Z",
            },
            {
                "id": 24,
                "project": project,
                "version": version,
                "query": "hello world",
                "created": "2019-06-11T18:00:00Z",
                "modified": "2019-06-11T18:00:00Z",
            },
            {
                "id": 25,
                "project": project,
                "version": version,
                "query": "hello world",
                "created": "2019-06-12T18:00:00Z",
                "modified": "2019-06-12T18:00:00Z",
            },
            {
                "id": 26,
                "project": project,
                "version": version,
                "query": "hello world",
                "created": "2019-07-02T18:00:00Z",
                "modified": "2019-07-02T18:00:00Z",
            },
            {
                "id": 27,
                "project": project,
                "version": version,
                "query": "hello world",
                "created": "2019-06-25T18:00:00Z",
                "modified": "2019-06-25T18:00:00Z",
            },
        ]
        for query in queries:
            SearchQuery.objects.get_or_create(**query)
            s = SearchQuery.objects.get(id=query["id"])
            s.created = timezone.make_aware(
                datetime.datetime.strptime(query["created"], "%Y-%m-%dT%H:%M:%SZ")
            )
            s.modified = timezone.make_aware(
                datetime.datetime.strptime(query["created"], "%Y-%m-%dT%H:%M:%SZ")
            )
            s.save()

    def handle(self, *args, **kwargs):
        self.load_data()
        self.stdout.write("Loaded search queries data")
