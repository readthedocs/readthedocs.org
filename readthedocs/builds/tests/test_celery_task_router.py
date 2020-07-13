import django_dynamic_fixture as fixture
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.models import Build, Version
from readthedocs.builds.tasks import TaskRouter
from readthedocs.projects.models import Project

class TaskRouterTests(TestCase):

    def setUp(self):
        self.project = fixture.get(
            Project,
            build_queue=None,
        )
        self.version = self.project.versions.first()
        self.build = fixture.get(
            Build,
            version=self.version,
        )
        for _ in range(TaskRouter.N_BUILDS + 5):
            fixture.get(
                Build,
                version=self.version,

            )

        self.task = 'readthedocs.projects.tasks.update_docs_task'
        self.args = (
            self.version.pk,
        )
        self.kwargs = {
            'build_pk': self.build.pk,
        }
        self.router = TaskRouter()

    def test_project_custom_queue(self):
        self.project.build_queue = 'build:custom'
        self.project.save()

        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            'build:custom',
        )

    def test_used_conda_in_last_builds(self):
        self.build._config = {'conda': {'file': 'docs/environment.yml'}}
        self.build.save()

        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            TaskRouter.BUILD_LARGE_QUEUE,
        )

    def test_more_than_n_builds(self):
        self.assertIsNone(
            self.router.route_for_task(self.task, self.args, self.kwargs),
        )

    def test_non_build_task(self):
        self.assertIsNone(
            self.router.route_for_task('non_build_task', self.args, self.kwargs),
        )

    def test_no_build_pk(self):
        self.assertIsNone(
            self.router.route_for_task(self.task, self.args, {}),
        )
