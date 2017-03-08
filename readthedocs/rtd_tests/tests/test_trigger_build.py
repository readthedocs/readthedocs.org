import mock

from django.test import TestCase

from core.utils import trigger_build
from projects.models import Project
from builds.models import Build, Version


class TestProject(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.latest = Version.objects.create(slug='latest', project=self.pip)

    def test_rate_limiting(self):
        for x in range(6):
            Build.objects.create(project=self.pip, version=self.latest)

        # Don't actually run update_docs
        with mock.patch('projects.tasks.update_docs'):

            with self.settings(BUILD_RATE_LIMIT=5):
                ret = trigger_build(project=self.pip)
                self.assertEqual(ret, None)

            with self.settings(BUILD_RATE_LIMIT=10):
                ret = trigger_build(project=self.pip)
                self.assertEqual(ret.__class__, Build)
