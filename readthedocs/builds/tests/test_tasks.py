from datetime import datetime, timedelta
from textwrap import dedent
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BRANCH,
    BUILD_STATE_FINISHED,
    BUILD_STATE_TRIGGERED,
    EXTERNAL,
    EXTERNAL_VERSION_STATE_CLOSED,
    EXTERNAL_VERSION_STATE_OPEN,
    LATEST,
    TAG,
)
from readthedocs.builds.models import Build, BuildCommandResult, BuildConfig, Version
from readthedocs.builds.tasks import (
    archive_builds_task,
    check_and_disable_project_for_consecutive_failed_builds,
    delete_closed_external_versions,
    delete_old_build_objects,
    post_build_overview,
    remove_orphan_build_config,
)
from readthedocs.filetreediff.dataclasses import FileTreeDiff, FileTreeDiffFileStatus
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteRepository,
)
from readthedocs.oauth.services import GitHubAppService
from readthedocs.projects.models import Project
from readthedocs.projects.notifications import (
    MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES,
)


class TestTasks(TestCase):
    def test_delete_closed_external_versions(self):
        project = get(Project)
        project.versions.all().delete()
        get(
            Version,
            project=project,
            slug="branch",
            type=BRANCH,
            state=EXTERNAL_VERSION_STATE_CLOSED,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug="tag",
            type=TAG,
            state=EXTERNAL_VERSION_STATE_OPEN,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug="external-active",
            type=EXTERNAL,
            state=EXTERNAL_VERSION_STATE_OPEN,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug="external-inactive",
            type=EXTERNAL,
            state=EXTERNAL_VERSION_STATE_CLOSED,
            modified=datetime.now() - timedelta(days=3),
        )
        get(
            Version,
            project=project,
            slug="external-inactive-old",
            type=EXTERNAL,
            state=EXTERNAL_VERSION_STATE_CLOSED,
            modified=datetime.now() - timedelta(days=7),
        )

        self.assertEqual(Version.objects.all().count(), 5)
        self.assertEqual(Version.external.all().count(), 3)

        # We don't have inactive external versions from 9 days ago.
        delete_closed_external_versions(days=9)
        self.assertEqual(Version.objects.all().count(), 5)
        self.assertEqual(Version.external.all().count(), 3)

        # We have one inactive external versions from 6 days ago.
        delete_closed_external_versions(days=6)
        self.assertEqual(Version.objects.all().count(), 4)
        self.assertEqual(Version.external.all().count(), 2)
        self.assertFalse(Version.objects.filter(slug="external-inactive-old").exists())

    @override_settings(RTD_SAVE_BUILD_COMMANDS_TO_STORAGE=True)
    @mock.patch("readthedocs.builds.models.build_commands_storage")
    def test_archive_builds(self, build_commands_storage):
        project = get(Project)
        version = get(Version, project=project)
        for i in range(10):
            date = timezone.now() - timezone.timedelta(days=i)
            build = get(
                Build,
                project=project,
                version=version,
                date=date,
                cold_storage=False,
            )
            for _ in range(10):
                get(
                    BuildCommandResult,
                    build=build,
                    command="ls",
                    output="docs",
                )

        self.assertEqual(Build.objects.count(), 10)
        self.assertEqual(BuildCommandResult.objects.count(), 100)

        archive_builds_task.delay(days=5)

        self.assertEqual(len(build_commands_storage.save.mock_calls), 5)
        self.assertEqual(Build.objects.count(), 10)
        self.assertEqual(Build.objects.filter(cold_storage=True).count(), 5)
        self.assertEqual(BuildCommandResult.objects.count(), 50)

    def _create_builds(self, project, version, count, success=False):
        """Helper to create a series of builds."""
        builds = []
        for _ in range(count):
            build = get(
                Build,
                project=project,
                version=version,
                success=success,
                state=BUILD_STATE_FINISHED,
            )
            builds.append(build)
        return builds

    @override_settings(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES=50)
    def test_task_disables_project_at_max_consecutive_failed_builds(self):
        """Test that the project is disabled at the failure threshold."""
        project = get(Project, slug="test-project", n_consecutive_failed_builds=False)
        version = project.versions.get(slug=LATEST)
        version.active = True
        version.save()

        # Create failures at the threshold
        self._create_builds(project, version, settings.RTD_BUILDS_MAX_CONSECUTIVE_FAILURES + 1, success=False)

        # Call the Celery task directly
        check_and_disable_project_for_consecutive_failed_builds(
            project_slug=project.slug,
            version_slug=version.slug,
        )

        project.refresh_from_db()
        self.assertTrue(project.n_consecutive_failed_builds)

        # Verify notification was added
        notification = Notification.objects.filter(
            message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES
        ).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.attached_to, project)

    @override_settings(RTD_BUILDS_MAX_CONSECUTIVE_FAILURES=50)
    def test_task_does_not_disable_project_with_successful_build(self):
        """Test that the project is NOT disabled when there's at least one successful build."""
        project = get(Project, slug="test-project-success", n_consecutive_failed_builds=False)
        version = project.versions.get(slug=LATEST)
        version.active = True
        version.save()

        # Create failures below the threshold with one successful build
        self._create_builds(project, version, settings.RTD_BUILDS_MAX_CONSECUTIVE_FAILURES - 1, success=False)
        self._create_builds(project, version, 1, success=True)  # One successful build
        self._create_builds(project, version, 1, success=False)  # One more failure

        # Call the Celery task directly
        check_and_disable_project_for_consecutive_failed_builds(
            project_slug=project.slug,
            version_slug=version.slug,
        )

        project.refresh_from_db()
        self.assertFalse(project.n_consecutive_failed_builds)

        # Verify notification was NOT added
        self.assertFalse(
            Notification.objects.filter(
                message_id=MESSAGE_PROJECT_BUILDS_DISABLED_DUE_TO_CONSECUTIVE_FAILURES,
            ).exists()
        )

    def test_remove_orphan_build_config(self):
        """Test that orphan BuildConfig objects are deleted."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create BuildConfig objects
        config_with_build = get(BuildConfig, data={"version": 2, "build": {"os": "ubuntu-20.04"}})
        orphan_config_1 = get(BuildConfig, data={"version": 2, "build": {"os": "ubuntu-22.04"}})
        orphan_config_2 = get(BuildConfig, data={"version": 2, "build": {"os": "ubuntu-24.04"}})

        # Create a Build and manually assign the BuildConfig
        build = get(Build, project=project, version=version)
        build.readthedocs_yaml_config = config_with_build
        build.save()

        # Verify the relationship is set correctly
        build.refresh_from_db()
        assert build.readthedocs_yaml_config == config_with_build
        assert config_with_build.builds.count() == 1

        # Verify initial state - we have at least our 3 BuildConfigs
        assert BuildConfig.objects.count() >= 3
        assert BuildConfig.objects.filter(pk=config_with_build.pk).exists()
        assert BuildConfig.objects.filter(pk=orphan_config_1.pk).exists()
        assert BuildConfig.objects.filter(pk=orphan_config_2.pk).exists()

        # Call the task
        remove_orphan_build_config()

        # Verify that only orphan configs were deleted
        # The config_with_build should still exist because it has a build
        assert BuildConfig.objects.filter(pk=config_with_build.pk).exists()
        # The orphan configs should be deleted
        assert not BuildConfig.objects.filter(pk=orphan_config_1.pk).exists()
        assert not BuildConfig.objects.filter(pk=orphan_config_2.pk).exists()

    def test_remove_orphan_build_config_no_orphans(self):
        """Test that no BuildConfig objects are deleted when there are no orphans."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create BuildConfig objects
        config_1 = get(BuildConfig, data={"version": 2, "build": {"os": "ubuntu-20.04"}})
        config_2 = get(BuildConfig, data={"version": 2, "build": {"os": "ubuntu-22.04"}})

        # Create Builds and manually assign the BuildConfig objects
        build_1 = get(Build, project=project, version=version)
        build_1.readthedocs_yaml_config = config_1
        build_1.save()

        build_2 = get(Build, project=project, version=version)
        build_2.readthedocs_yaml_config = config_2
        build_2.save()

        # Verify initial state
        assert BuildConfig.objects.count() >= 2
        assert BuildConfig.objects.filter(pk=config_1.pk).exists()
        assert BuildConfig.objects.filter(pk=config_2.pk).exists()

        # Call the task
        remove_orphan_build_config()

        # Verify that no configs were deleted
        assert BuildConfig.objects.filter(pk=config_1.pk).exists()
        assert BuildConfig.objects.filter(pk=config_2.pk).exists()


class TestDeleteOldBuildObjects(TestCase):
    def _create_old_build(self, project, version, days_old, state=BUILD_STATE_FINISHED, cold_storage=False):
        """Create a build with a specific age."""
        build = get(
            Build,
            project=project,
            version=version,
            state=state,
            cold_storage=cold_storage,
        )
        # Override the auto-set date with a specific old date.
        Build.objects.filter(pk=build.pk).update(
            date=timezone.now() - timezone.timedelta(days=days_old)
        )
        return build

    def test_old_builds_beyond_keep_recent_are_deleted(self):
        """Builds older than `days` and beyond `keep_recent` per version are deleted."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create 5 old builds with different ages so ordering is deterministic.
        old_builds = [self._create_old_build(project, version, days_old=400 + i) for i in range(5)]

        assert Build.objects.filter(version=version).count() == 5

        # Keep 2 recent builds per version, so 3 should be deleted.
        delete_old_build_objects.delay(days=365, keep_recent=2, start=0)

        assert Build.objects.filter(version=version).count() == 2
        # The 2 most-recently-dated builds (those with the smallest days_old) should be kept.
        remaining_pks = set(
            Build.objects.filter(version=version).values_list("pk", flat=True)
        )
        assert remaining_pks == {old_builds[0].pk, old_builds[1].pk}

    def test_recent_builds_are_not_deleted(self):
        """Builds newer than `days` threshold are never deleted."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create builds that are recent (within 'days' cutoff).
        for _ in range(5):
            get(Build, project=project, version=version, state=BUILD_STATE_FINISHED)

        assert Build.objects.filter(version=version).count() == 5

        delete_old_build_objects.delay(days=365, keep_recent=2, start=0)

        # None should be deleted since they are all recent.
        assert Build.objects.filter(version=version).count() == 5

    def test_builds_within_keep_recent_are_not_deleted(self):
        """The most recent `keep_recent` builds per version are never deleted, even if old."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create 3 old builds.
        for _ in range(3):
            self._create_old_build(project, version, days_old=400)

        assert Build.objects.filter(version=version).count() == 3

        # keep_recent=5 means all 3 should be preserved.
        delete_old_build_objects.delay(days=365, keep_recent=5, start=0)

        assert Build.objects.filter(version=version).count() == 3

    def test_non_final_state_builds_deleted(self):
        """Builds in non-final states (e.g. triggered) are never deleted."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create old builds in a non-final state.
        for _ in range(5):
            self._create_old_build(project, version, days_old=400, state=BUILD_STATE_TRIGGERED)

        assert Build.objects.filter(version=version).count() == 5

        delete_old_build_objects.delay(days=365, keep_recent=0, start=0)

        # Non-final builds should be deleted.
        assert Build.objects.filter(version=version).count() == 0

    def test_versionless_builds_deleted(self):
        """Old builds without a version are also deleted, beyond `keep_recent` per project."""
        project = get(Project)

        # Create 5 old versionless builds with different ages so ordering is deterministic.
        old_builds = [
            self._create_old_build(project, version=None, days_old=400 + i) for i in range(5)
        ]

        assert Build.objects.filter(project=project, version=None).count() == 5

        delete_old_build_objects.delay(days=365, keep_recent=2, start=0)

        # 3 should be deleted (keeping only 2 most recent).
        assert Build.objects.filter(project=project, version=None).count() == 2
        remaining_pks = set(
            Build.objects.filter(project=project, version=None).values_list("pk", flat=True)
        )
        assert remaining_pks == {old_builds[0].pk, old_builds[1].pk}

    def test_limit_stops_deletion(self):
        """Deletion stops once `limit` builds have been deleted."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        for _ in range(10):
            self._create_old_build(project, version, days_old=400)

        assert Build.objects.filter(version=version).count() == 10

        # With limit=3 and keep_recent=0, only 3 builds should be deleted.
        delete_old_build_objects.delay(days=365, keep_recent=0, limit=3, start=0)

        assert Build.objects.filter(version=version).count() == 7

    def test_max_projects_limits_projects_processed(self):
        """Only `max_projects` projects are processed per execution."""
        project1 = get(Project)
        project2 = get(Project)
        version1 = project1.versions.get(slug=LATEST)
        version2 = project2.versions.get(slug=LATEST)

        for _ in range(5):
            self._create_old_build(project1, version1, days_old=400)
        for _ in range(5):
            self._create_old_build(project2, version2, days_old=400)

        # Only process 1 project at a time (max_projects=1).
        delete_old_build_objects.delay(days=365, keep_recent=0, max_projects=1, start=0)

        total_remaining = (
            Build.objects.filter(version=version1).count()
            + Build.objects.filter(version=version2).count()
        )
        # Only one project's builds were processed.
        assert total_remaining == 5

    def test_keeps_builds_per_version_independently(self):
        """keep_recent applies independently to each version."""
        project = get(Project)
        version1 = project.versions.get(slug=LATEST)
        version2 = get(Version, project=project, slug="stable")

        for _ in range(5):
            self._create_old_build(project, version1, days_old=400)
        for _ in range(5):
            self._create_old_build(project, version2, days_old=400)

        delete_old_build_objects.delay(days=365, keep_recent=2, start=0)

        # Each version should retain 2 builds.
        assert Build.objects.filter(version=version1).count() == 2
        assert Build.objects.filter(version=version2).count() == 2

    @mock.patch("readthedocs.builds.tasks.build_commands_storage")
    def test_cold_storage_paths_are_deleted(self, build_commands_storage):
        """Cold storage paths of deleted builds are removed."""
        project = get(Project)
        version = project.versions.get(slug=LATEST)

        # Create old builds in cold storage.
        for _ in range(3):
            self._create_old_build(project, version, days_old=400, cold_storage=True)
        # Also create 2 recent builds in cold storage (should NOT be deleted).
        for _ in range(2):
            get(Build, project=project, version=version, state=BUILD_STATE_FINISHED, cold_storage=True)

        delete_old_build_objects.delay(days=365, keep_recent=0, start=0)

        # All 3 old builds should have been deleted.
        assert Build.objects.filter(version=version).count() == 2
        # Storage delete should have been called for each deleted build's path.
        build_commands_storage.delete_paths.assert_called()


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    PUBLIC_DOMAIN="readthedocs.io",
    RTD_EXTERNAL_VERSION_DOMAIN="readthedocs.build",
)
class TestPostBuildOverview(TestCase):

    def setUp(self):
        self.user = get(User)
        self.github_app_installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=1111,
            target_type=GitHubAccountType.USER,
        )
        self.remote_repository = get(
            RemoteRepository,
            name="repo",
            full_name="user/repo",
            vcs_provider=GITHUB_APP,
            github_app_installation=self.github_app_installation,
        )

        self.project = get(
            Project,
            name="My project",
            slug="my-project",
            users=[self.user],
            remote_repository=self.remote_repository,
        )
        self.base_version = self.project.versions.get(slug=LATEST)
        self.base_version.built = True
        self.base_version.save()
        self.base_version_build = get(
            Build,
            project=self.project,
            version=self.base_version,
            commit="1234abcd",
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        self.current_version = get(
            Version,
            project=self.project,
            verbose_name="1",
            slug="1",
            type=EXTERNAL,
            active=True,
            built=True,
        )
        self.current_version_build = get(
            Build,
            project=self.project,
            version=self.current_version,
            commit="5678abcd",
            state=BUILD_STATE_FINISHED,
            success=True,
        )

    @mock.patch.object(GitHubAppService, "post_comment")
    @mock.patch("readthedocs.builds.reporting.get_diff")
    def test_post_build_overview(self, get_diff, post_comment):
        get_diff.return_value = FileTreeDiff(
            current_version=self.current_version,
            current_version_build=self.current_version_build,
            base_version=self.base_version,
            base_version_build=self.base_version_build,
            files=[
                ("index.html", FileTreeDiffFileStatus.modified),
                ("changes.html", FileTreeDiffFileStatus.added),
                ("deleteme.html", FileTreeDiffFileStatus.deleted),
            ],
            outdated=False,
        )
        post_build_overview(build_pk=self.current_version_build.pk)
        expected_comment = dedent(
            f"""
            ### Documentation build overview

            > 📚 [My project](https://readthedocs.org/projects/my-project/) | 🛠️ Build [#{self.current_version_build.id}](https://readthedocs.org/projects/my-project/builds/{self.current_version_build.id}/) | 📁 Comparing 5678abcd against [latest](http://my-project.readthedocs.io/en/latest/) (1234abcd)

            [<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>](http://my-project--1.readthedocs.build/en/1/)


            <details>
            <summary>Show files changed (3 files in total): 📝 1 modified | ➕ 1 added | ➖ 1 deleted</summary>

            | File | Status |
            | --- | --- |
            | [changes.html](http://my-project--1.readthedocs.build/en/1/changes.html) | ➕ added |
            | [deleteme.html](http://my-project--1.readthedocs.build/en/1/deleteme.html) | ➖ deleted |
            | [index.html](http://my-project--1.readthedocs.build/en/1/index.html) | 📝 modified |


            </details>

            """
        )
        post_comment.assert_called_once_with(
            build=self.current_version_build,
            comment=expected_comment,
            create_new=True,
        )

    @mock.patch.object(GitHubAppService, "post_comment")
    @mock.patch("readthedocs.builds.reporting.get_diff")
    def test_post_build_overview_more_than_5_files(self, get_diff, post_comment):
        get_diff.return_value = FileTreeDiff(
            current_version=self.current_version,
            current_version_build=self.current_version_build,
            base_version=self.base_version,
            base_version_build=self.base_version_build,
            files=[
                ("index.html", FileTreeDiffFileStatus.modified),
                ("changes.html", FileTreeDiffFileStatus.added),
                ("deleteme.html", FileTreeDiffFileStatus.deleted),
                ("one.html", FileTreeDiffFileStatus.modified),
                ("three.html", FileTreeDiffFileStatus.modified),
                ("two.html", FileTreeDiffFileStatus.modified),
            ],
            outdated=False,
        )
        post_build_overview(build_pk=self.current_version_build.pk)
        expected_comment = dedent(
            f"""
            ### Documentation build overview

            > 📚 [My project](https://readthedocs.org/projects/my-project/) | 🛠️ Build [#{self.current_version_build.id}](https://readthedocs.org/projects/my-project/builds/{self.current_version_build.id}/) | 📁 Comparing 5678abcd against [latest](http://my-project.readthedocs.io/en/latest/) (1234abcd)

            [<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>](http://my-project--1.readthedocs.build/en/1/)


            <details>
            <summary>Show files changed (6 files in total): 📝 4 modified | ➕ 1 added | ➖ 1 deleted</summary>

            | File | Status |
            | --- | --- |
            | [changes.html](http://my-project--1.readthedocs.build/en/1/changes.html) | ➕ added |
            | [deleteme.html](http://my-project--1.readthedocs.build/en/1/deleteme.html) | ➖ deleted |
            | [index.html](http://my-project--1.readthedocs.build/en/1/index.html) | 📝 modified |
            | [one.html](http://my-project--1.readthedocs.build/en/1/one.html) | 📝 modified |
            | [three.html](http://my-project--1.readthedocs.build/en/1/three.html) | 📝 modified |
            | [two.html](http://my-project--1.readthedocs.build/en/1/two.html) | 📝 modified |


            </details>

            """
        )

        post_comment.assert_called_once_with(
            build=self.current_version_build,
            comment=expected_comment,
            create_new=True,
        )

    @mock.patch.object(GitHubAppService, "post_comment")
    @mock.patch("readthedocs.builds.reporting.get_diff")
    def test_post_build_overview_no_files_changed(self, get_diff, post_comment):
        get_diff.return_value = FileTreeDiff(
            current_version=self.current_version,
            current_version_build=self.current_version_build,
            base_version=self.base_version,
            base_version_build=self.base_version_build,
            files=[],
            outdated=False,
        )
        post_build_overview(build_pk=self.current_version_build.pk)
        expected_comment = dedent(
            f"""
            ### Documentation build overview

            > 📚 [My project](https://readthedocs.org/projects/my-project/) | 🛠️ Build [#{self.current_version_build.id}](https://readthedocs.org/projects/my-project/builds/{self.current_version_build.id}/) | 📁 Comparing 5678abcd against [latest](http://my-project.readthedocs.io/en/latest/) (1234abcd)

            [<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>](http://my-project--1.readthedocs.build/en/1/)


            No files changed.

            """
        )

        post_comment.assert_called_once_with(
            build=self.current_version_build,
            comment=expected_comment,
            create_new=False,
        )

    @mock.patch.object(GitHubAppService, "post_comment")
    def test_post_build_overview_no_external_version(self, post_comment):
        assert not self.base_version.is_external
        post_build_overview(build_pk=self.base_version_build.pk)
        post_comment.assert_not_called()

    @mock.patch.object(GitHubAppService, "post_comment")
    def test_post_build_overview_no_github_app_project(self, post_comment):
        self.project.remote_repository = None
        self.project.save()

        assert not self.project.is_github_app_project
        assert self.current_version.is_external
        post_build_overview(build_pk=self.current_version_build.pk)
        post_comment.assert_not_called()

    @mock.patch.object(GitHubAppService, "post_comment")
    @mock.patch("readthedocs.builds.reporting.get_diff")
    def test_post_build_overview_no_diff_available(self, get_diff, post_comment):
        get_diff.return_value = None
        assert self.current_version.is_external
        post_build_overview(build_pk=self.current_version_build.pk)
        post_comment.assert_not_called()
