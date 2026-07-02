from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class BuildQueueTimeTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def test_queue_time_defaults_to_none(self):
        # Builds triggered before queue time was tracked have no value.
        build = get(Build, project=self.project, version=self.version, queue_time=None)
        assert build.queue_time is None

    def test_queue_time_is_stored_independently_from_duration(self):
        # Queue wait time is stored separately so it does not inflate the
        # build duration (``length``).
        build = get(
            Build,
            project=self.project,
            version=self.version,
            queue_time=30,
            length=60,
        )
        build.refresh_from_db()
        assert build.queue_time == 30
        assert build.length == 60
