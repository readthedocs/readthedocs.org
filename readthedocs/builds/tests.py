import django_dynamic_fixture as fixture
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.builds.tasks import TaskRouter
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project, Feature



class TaskRouterTests(TestCase):

    def setUp(self):
        self.project = fixture.get(
            Project,
            build_queue=None,
        )
        self.feature = fixture.get(
            Feature,
            feature_id=Feature.CELERY_ROUTER,
        )
        self.feature.projects.add(self.project)
        self.version = self.project.versions.first()
        self.build = fixture.get(
            Build,
            version=self.version,
        )
        for _ in range(TaskRouter.n_builds + 5):
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

    def test_not_under_feature_flag(self):
        self.feature.projects.remove(self.project)
        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            settings.CELERY_DEFAULT_QUEUE,
        )

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
        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            settings.CELERY_DEFAULT_QUEUE,
        )

    def test_non_build_task(self):
        self.assertEqual(
            self.router.route_for_task('non_build_task', self.args, self.kwargs),
            None,
        )

    def test_no_build_pk(self):
        self.assertEqual(
            self.router.route_for_task(self.task, self.args, {}),
            settings.CELERY_DEFAULT_QUEUE,
        )

    def test_build_length_high_average(self):
        high_length = TaskRouter.time_average + 50
        self.version.builds.update(length=high_length)
        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            TaskRouter.BUILD_LARGE_QUEUE,
        )
