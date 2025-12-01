"""Tests for build signal receivers."""

from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.builds.signals_receivers import (
    RTD_BUILDS_MAX_CONSECUTIVE_FAILURES,
    _count_consecutive_failed_builds,
    disable_project_on_consecutive_failed_builds,
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

    def test_count_consecutive_failed_builds_no_builds(self):
        """Test counting failures when there are no builds."""
        count = _count_consecutive_failed_builds(self.project, self.version.slug)
        self.assertEqual(count, 0)

    def test_count_consecutive_failed_builds_all_success(self):
        """Test counting failures when all builds succeeded."""
        self._create_builds(10, success=True)
        count = _count_consecutive_failed_builds(self.project, self.version.slug)
        self.assertEqual(count, 0)

    def test_count_consecutive_failed_builds_all_failures(self):
        """Test counting failures when all builds failed."""
        self._create_builds(25, success=False)
        count = _count_consecutive_failed_builds(self.project, self.version.slug)
        self.assertEqual(count, 25)

    def test_count_consecutive_failed_builds_mixed(self):
        """Test counting failures when there's a mix of success and failures."""
        # Create successful builds first (older)
        self._create_builds(5, success=True)
        # Create failed builds after (newer)
        self._create_builds(10, success=False)

        count = _count_consecutive_failed_builds(self.project, self.version.slug)
        self.assertEqual(count, 10)

    def test_count_consecutive_failed_builds_success_breaks_streak(self):
        """Test that a successful build breaks the consecutive failure streak."""
        # Create failed builds first (older)
        self._create_builds(10, success=False)
        # Create one successful build (newer)
        self._create_builds(1, success=True)
        # Create more failed builds (newest)
        self._create_builds(5, success=False)

        count = _count_consecutive_failed_builds(self.project, self.version.slug)
        self.assertEqual(count, 5)

    def test_signal_handler_does_nothing_on_success(self):
        """Test that the signal handler does nothing when build succeeds."""
        # Create many failed builds to be at the threshold
        many_failed_builds = RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 50
        self._create_builds(many_failed_builds, success=False)

        # Simulate a successful build completion
        build_dict = {
            "success": True,
            "project": self.project.pk,
            "version_slug": self.version.slug,
        }
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )

        self.project.refresh_from_db()
        self.assertFalse(self.project.skip)

    def test_signal_handler_does_nothing_on_non_default_version(self):
        """Test that the signal handler only checks the default version."""
        # Create a different version
        other_version = get(
            Version,
            project=self.project,
            slug="other-version",
            active=True,
        )
        # Create many failed builds on the other version
        many_failed_builds = RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 50
        for _ in range(many_failed_builds):
            get(
                Build,
                project=self.project,
                version=other_version,
                success=False,
                state=BUILD_STATE_FINISHED,
            )

        # Simulate a failed build on the other version
        build_dict = {
            "success": False,
            "project": self.project.pk,
            "version_slug": other_version.slug,
        }
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )

        self.project.refresh_from_db()
        self.assertFalse(self.project.skip)

    def test_signal_handler_does_nothing_when_project_already_skipped(self):
        """Test that the signal handler does nothing when project is already skipped."""
        self.project.skip = True
        self.project.save()

        # Create many failed builds
        many_failed_builds = RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 50
        self._create_builds(many_failed_builds, success=False)

        build_dict = {
            "success": False,
            "project": self.project.pk,
            "version_slug": self.version.slug,
        }
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )

        # Verify no notification was added
        self.assertEqual(
            Notification.objects.filter(
                message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES
            ).count(),
            0,
        )

    @override_settings(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES=50)
    def test_signal_handler_does_not_disable_below_threshold(self):
        """Test that the project is not disabled below the failure threshold."""
        # Create failures just below the threshold
        self._create_builds(49, success=False)

        build_dict = {
            "success": False,
            "project": self.project.pk,
            "version_slug": self.version.slug,
        }
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )

        self.project.refresh_from_db()
        self.assertFalse(self.project.skip)
        self.assertEqual(
            Notification.objects.filter(
                message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES
            ).count(),
            0,
        )

    @override_settings(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES=50)
    def test_signal_handler_disables_at_threshold(self):
        """Test that the project is disabled at the failure threshold."""
        # Create failures at the threshold
        self._create_builds(50, success=False)

        build_dict = {
            "success": False,
            "project": self.project.pk,
            "version_slug": self.version.slug,
        }
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )

        self.project.refresh_from_db()
        self.assertTrue(self.project.skip)

        # Verify notification was added
        notification = Notification.objects.filter(
            message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.attached_to, self.project)

    def test_signal_handler_handles_build_instance(self):
        """Test that the signal handler ignores Build instances (not dicts)."""
        # The signal sends dicts from the celery task, not Build instances.
        # This test ensures we handle the case if someone sends a Build instance.
        build = get(
            Build,
            project=self.project,
            version=self.version,
            success=False,
            state=BUILD_STATE_FINISHED,
        )

        # Should not raise any exception
        disable_project_on_consecutive_failed_builds(sender=Build, build=build)

        self.project.refresh_from_db()
        self.assertFalse(self.project.skip)

    def test_signal_handler_handles_missing_project(self):
        """Test that the signal handler handles missing project gracefully."""
        build_dict = {
            "success": False,
            "project": 99999,  # Non-existent project ID
            "version_slug": self.version.slug,
        }

        # Should not raise any exception
        disable_project_on_consecutive_failed_builds(
            sender=Build, build=build_dict
        )


class TestDefaultConfigValue(TestCase):
    def test_default_threshold_value(self):
        """Test that the default threshold is 50."""
        # Check that the default value is correctly set
        self.assertEqual(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES, 50)
