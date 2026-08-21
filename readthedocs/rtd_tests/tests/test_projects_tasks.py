import datetime

from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BUILD_STATUS_SUCCESS,
    BUILD_STATE_CLONING,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_TRIGGERED,
    EXTERNAL,
)
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Feature, Project
from readthedocs.projects.tasks.utils import finish_unhealthy_builds, send_external_build_status


class SendBuildStatusTests(TestCase):
    def setUp(self):
        self.project = get(Project)
        self.internal_version = get(Version, project=self.project)
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build, project=self.project, version=self.external_version
        )
        self.internal_build = get(
            Build, project=self.project, version=self.internal_version
        )

    @patch("readthedocs.projects.tasks.utils.send_build_status")
    def test_send_external_build_status_with_external_version(self, send_build_status):
        send_external_build_status(
            self.external_version.type,
            self.external_build.id,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS,
        )

        send_build_status.delay.assert_called_once_with(
            self.external_build.id,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS,
        )

    @patch("readthedocs.projects.tasks.utils.send_build_status")
    def test_send_external_build_status_with_internal_version(self, send_build_status):
        send_external_build_status(
            self.internal_version.type,
            self.internal_build.id,
            self.external_build.commit,
            BUILD_STATUS_SUCCESS,
        )

        send_build_status.delay.assert_not_called()

class TestFinishInactiveBuildsTask(TestCase):

    @patch("readthedocs.projects.tasks.utils.app")
    def test_finish_unhealthy_builds_task(self, mocked_app):
        project = get(Project)
        feature = get(Feature, feature_id=Feature.BUILD_HEALTHCHECK)
        feature.projects.add(project)

        # Build just started with the default time and healthcheck now
        build_1 = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_CLONING,
            healthcheck=timezone.now(),
        )

        # Build started an hour ago with default time and healthcheck 59s ago
        build_2 = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
            date=timezone.now() - datetime.timedelta(hours=1),
            healthcheck=timezone.now() - datetime.timedelta(seconds=59),
        )

        # Build started an hour ago with custom time (2 hours) and healthcheck 15m ago
        build_3 = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
            date=timezone.now() - datetime.timedelta(hours=2),
            healthcheck=timezone.now() - datetime.timedelta(minutes=15),
        )

        finish_unhealthy_builds()

        build_1.refresh_from_db()
        self.assertEqual(build_1.state, BUILD_STATE_CLONING)

        build_2.refresh_from_db()
        self.assertEqual(build_2.state, BUILD_STATE_TRIGGERED)

        build_3.refresh_from_db()
        self.assertEqual(build_3.state, BUILD_STATE_CANCELLED)
        self.assertEqual(build_3.success, False)
        self.assertEqual(build_3.notifications.count(), 1)
