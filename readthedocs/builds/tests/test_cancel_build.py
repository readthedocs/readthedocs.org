from unittest import mock

from django.test import TestCase

from readthedocs.builds.constants import (
    BUILD_STATE_TRIGGERED,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_BUILDING,
    BUILD_FINAL_STATES,
)
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import cancel_build
from readthedocs.projects.models import Project


class CancelBuildTests(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Test project",
            slug="test-project",
            repo="https://example.com/repo.git",
        )
        self.version = Version.objects.create(
            project=self.project,
            slug="latest",
            verbose_name="latest",
            type="branch",
            identifier="main",
            active=True,
        )

    @mock.patch("readthedocs.core.utils.app.control.revoke")
    def test_cancel_triggered_build_sets_cancelled_state(self, revoke):
        build = Build.objects.create(
            project=self.project,
            version=self.version,
            state=BUILD_STATE_TRIGGERED,
            success=True,
            task_id="dummy-task-id",
        )

        cancel_build(build)
        build.refresh_from_db()

        # Build must be cancelled and considered final
        self.assertEqual(build.state, BUILD_STATE_CANCELLED)
        self.assertIn(build.state, BUILD_FINAL_STATES)

        # Build must no longer be active
        active_ids = Build.objects.exclude(
            state__in=BUILD_FINAL_STATES,
        ).values_list("id", flat=True)
        self.assertNotIn(build.id, active_ids)

        # Celery revoke should be called with terminate=False
        revoke.assert_called_once_with(
            "dummy-task-id",
            signal="SIGINT",
            terminate=False
        )

    @mock.patch("readthedocs.core.utils.app.control.revoke")
    def test_cancel_running_or_retry_build_sets_cancelled_state(self, revoke):
        # Use BUILD_STATE_BUILDING to simulate a running build
        build = Build.objects.create(
            project=self.project,
            version=self.version,
            state=BUILD_STATE_BUILDING,
            success=True,
            task_id="dummy-task-id-2",
        )

        cancel_build(build)
        build.refresh_from_db()

        self.assertEqual(build.state, BUILD_STATE_CANCELLED)
        self.assertIn(build.state, BUILD_FINAL_STATES)

        active_ids = Build.objects.exclude(
            state__in=BUILD_FINAL_STATES,
        ).values_list("id", flat=True)
        self.assertNotIn(build.id, active_ids)

        # Running builds should be terminated=True
        revoke.assert_called_once_with(
            "dummy-task-id-2",
            signal="SIGINT",
            terminate=True
        )
