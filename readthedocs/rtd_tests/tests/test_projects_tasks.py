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
from readthedocs.projects.models import Project
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

    @patch("readthedocs.projects.tasks.utils.app")
    def test_finish_unhealthy_builds_reaps_lost_dispatched_builds(self, mocked_app):
        """
        A build dispatched to the isolated fleet but never picked up is "lost".

        It's cancelled once it's been ``triggered`` with a ``dispatched_date``
        older than ``RTD_BUILD_DISPATCH_TIMEOUT``. Recently-dispatched builds
        and genuinely-queued builds (no ``dispatched_date``) are left alone.
        """
        project = get(Project)

        # Dispatched to the fleet long ago but never picked up -> lost.
        lost = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
            healthcheck=None,
            dispatched_date=timezone.now() - datetime.timedelta(minutes=10),
        )

        # Dispatched recently, still within the timeout -> keep waiting.
        recent = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
            healthcheck=None,
            dispatched_date=timezone.now() - datetime.timedelta(seconds=30),
        )

        # Genuinely queued, never dispatched -> leave it for the admission task.
        queued = get(
            Build,
            project=project,
            version=project.get_stable_version(),
            state=BUILD_STATE_TRIGGERED,
            healthcheck=None,
            dispatched_date=None,
        )

        finish_unhealthy_builds()

        lost.refresh_from_db()
        assert lost.state == BUILD_STATE_CANCELLED
        assert lost.success is False
        assert lost.notifications.count() == 1

        recent.refresh_from_db()
        assert recent.state == BUILD_STATE_TRIGGERED

        queued.refresh_from_db()
        assert queued.state == BUILD_STATE_TRIGGERED

    @patch("readthedocs.projects.tasks.utils.app")
    def test_finish_unhealthy_builds_reaps_builds_that_never_healthchecked(self, mocked_app):
        """
        A build a builder picked up but that never sent a healthcheck is dead.

        It's cancelled once it's past ``triggered`` with no ``healthcheck`` and
        older than ``RTD_BUILD_START_TIMEOUT``. Builds that just started, and
        ``triggered`` builds still waiting in the queue, are left alone.
        """
        project = get(Project)

        def build(state, age):
            build = get(
                Build,
                project=project,
                version=project.get_stable_version(),
                state=state,
                healthcheck=None,
                dispatched_date=None,
            )
            # ``date`` is ``auto_now_add``, so it has to be updated after creation.
            Build.objects.filter(pk=build.pk).update(date=timezone.now() - age)
            return build

        # Picked up by a builder long ago, never pinged -> dead.
        dead = build(BUILD_STATE_CLONING, datetime.timedelta(hours=2))
        # Picked up by a builder recently, container still starting -> keep waiting.
        starting = build(BUILD_STATE_CLONING, datetime.timedelta(minutes=10))
        # Still queued, old but never picked up -> not this task's call.
        queued = build(BUILD_STATE_TRIGGERED, datetime.timedelta(hours=2))

        finish_unhealthy_builds()

        dead.refresh_from_db()
        assert dead.state == BUILD_STATE_CANCELLED
        assert dead.success is False
        assert dead.notifications.count() == 1

        starting.refresh_from_db()
        assert starting.state == BUILD_STATE_CLONING

        queued.refresh_from_db()
        assert queued.state == BUILD_STATE_TRIGGERED
