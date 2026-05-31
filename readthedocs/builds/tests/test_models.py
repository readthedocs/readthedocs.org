import datetime

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Build
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class BuildQueueTimeTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.version = get(Version, project=self.project)

    def test_queue_time_is_none_when_task_not_executed(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            task_executed_at=None,
        )
        assert build.queue_time is None

    def test_queue_time_is_time_between_trigger_and_execution(self):
        build = get(Build, project=self.project, version=self.version)
        build.task_executed_at = build.date + datetime.timedelta(seconds=120)
        assert build.queue_time == 120

    def test_queue_time_is_independent_from_duration(self):
        # Time spent queued should not be counted as part of the build duration.
        build = get(
            Build,
            project=self.project,
            version=self.version,
            length=42,
        )
        build.task_executed_at = build.date + datetime.timedelta(seconds=300)
        assert build.queue_time == 300
        assert build.length == 42
