"""Tests for build signal receivers."""

from django.conf import settings
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, LATEST
from readthedocs.builds.models import Build
from readthedocs.builds.tasks import (
    check_and_disable_project_for_consecutive_failed_builds,
)
from readthedocs.notifications.models import Notification
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import (
    MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES,
)


class TestDisableProjectOnConsecutiveFailedBuilds(TestCase):
    def setUp(self):
        self.project = get(Project, slug="test-project", skip=False)
        self.version = self.project.versions.get(slug=LATEST)
        self.version.active = True
        self.version.save()

    def _create_builds(self, count, success=False):
        """Helper to create a series of builds."""
        builds = []
        for _ in range(count):
            build = get(
                Build,
                project=self.project,
                version=self.version,
                success=success,
                state=BUILD_STATE_FINISHED,
            )
            builds.append(build)
        return builds

    @override_settings(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES=50)
    def test_task_disables_at_threshold(self):
        """Test that the project is disabled at the failure threshold."""
        # Create failures at the threshold
        self._create_builds(settings.RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 1, success=False)

        # Call the Celery task directly
        check_and_disable_project_for_consecutive_failed_builds(
            project_id=self.project.pk,
            version_slug=self.version.slug,
        )

        self.project.refresh_from_db()
        self.assertTrue(self.project.skip)

        # Verify notification was added
        notification = Notification.objects.filter(
            message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.attached_to, self.project)
