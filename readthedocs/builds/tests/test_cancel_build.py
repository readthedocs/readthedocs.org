from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_TRIGGERED,
)
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import cancel_build
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Project


class CancelBuildTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Cancel build project",
            slug="cancel-build-project",
            repo="https://example.com/repo.git",
        )
        self.version = self.project.versions.first()
        if self.version is None:
            self.version = Version.objects.create(
                project=self.project,
                identifier="main",
                verbose_name="main",
                slug="main",
                active=True,
            )

    @mock.patch("readthedocs.core.utils.app")
    def test_cancel_running_or_retry_build_sets_cancelled_state(self, app):
        build = Build.objects.create(
            project=self.project,
            version=self.version,
            task_id="1234",
            state=BUILD_STATE_BUILDING,
            success=True,
        )

        cancel_build(build)

        build.refresh_from_db()
        assert build.state == BUILD_STATE_CANCELLED
        assert build.success is False
        assert build.length is not None

        # A notification was created for this build (match by Generic FK)
        build_ct = ContentType.objects.get_for_model(build)
        assert Notification.objects.filter(
            attached_to_id=build.pk,
            attached_to_content_type=build_ct,
        ).exists()

        # Running build: terminate=True
        app.control.revoke.assert_called_once_with(
            build.task_id,
            signal=mock.ANY,
            terminate=True,
        )

    @mock.patch("readthedocs.core.utils.app")
    def test_cancel_triggered_build_sets_cancelled_state(self, app):
        build = Build.objects.create(
            project=self.project,
            version=self.version,
            task_id="1234",
            state=BUILD_STATE_TRIGGERED,
            success=True,
        )

        cancel_build(build)

        build.refresh_from_db()
        assert build.state == BUILD_STATE_CANCELLED
        assert build.success is False

        # Triggered (not yet running): terminate=False
        app.control.revoke.assert_called_once_with(
            build.task_id,
            signal=mock.ANY,
            terminate=False,
        )
