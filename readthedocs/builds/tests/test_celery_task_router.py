import django_dynamic_fixture as fixture
from django.test import TestCase

from readthedocs.builds.constants import EXTERNAL
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
            success=True,
        )
        for _ in range(TaskRouter.MIN_SUCCESSFUL_BUILDS + 5):
            fixture.get(
                Build,
                version=self.version,
            )

        self.task = "readthedocs.projects.tasks.builds.update_docs_task"
        self.args = (self.version.pk,)
        self.kwargs = {
            "build_pk": self.build.pk,
        }
        self.router = TaskRouter()

    def test_project_custom_queue(self):
        self.project.build_queue = "build:custom"
        self.project.save()

        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            "build:custom",
        )

    def test_used_conda_in_last_builds(self):
        self.build._config = {"conda": {"file": "docs/environment.yml"}}
        self.build.save()

        self.assertEqual(
            self.router.route_for_task(self.task, self.args, self.kwargs),
            TaskRouter.BUILD_LARGE_QUEUE,
        )

    def test_used_conda_in_last_failed_build(self):
        self.build._config = {"conda": {"file": "docs/environment.yml"}}
        self.build.success = False
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
            self.router.route_for_task("non_build_task", self.args, self.kwargs),
        )

    def test_no_build_pk(self):
        self.assertIsNone(
            self.router.route_for_task(self.task, self.args, {}),
        )

    def test_external_version(self):
        external_version = fixture.get(
            Version,
            project=self.project,
            slug="pull-request",
            type=EXTERNAL,
        )
        default_version = self.project.versions.get(
            slug=self.project.get_default_version()
        )
        default_version_build = fixture.get(
            Build,
            version=default_version,
            project=self.project,
            builder="build-default-a1b2c3",
        )
        args = (external_version.pk,)
        kwargs = {"build_pk": default_version_build.pk}

        self.assertEqual(
            self.router.route_for_task(self.task, args, kwargs),
            TaskRouter.BUILD_DEFAULT_QUEUE,
        )

        default_version_build.builder = "build-large-a1b2c3"
        default_version_build.save()

        self.assertEqual(
            self.router.route_for_task(self.task, args, kwargs),
            TaskRouter.BUILD_LARGE_QUEUE,
        )
