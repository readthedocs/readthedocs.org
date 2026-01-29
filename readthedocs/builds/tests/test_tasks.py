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
    @mock.patch("readthedocs.builds.tasks.build_commands_storage")
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

        archive_builds_task.delay(days=5, delete=True)

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
        self.assertEqual(build.readthedocs_yaml_config, config_with_build)
        self.assertEqual(config_with_build.builds.count(), 1)

        # Verify initial state - we have at least our 3 BuildConfigs
        self.assertGreaterEqual(BuildConfig.objects.count(), 3)
        self.assertTrue(BuildConfig.objects.filter(pk=config_with_build.pk).exists())
        self.assertTrue(BuildConfig.objects.filter(pk=orphan_config_1.pk).exists())
        self.assertTrue(BuildConfig.objects.filter(pk=orphan_config_2.pk).exists())

        # Call the task
        remove_orphan_build_config()

        # Verify that only orphan configs were deleted
        # The config_with_build should still exist because it has a build
        self.assertTrue(BuildConfig.objects.filter(pk=config_with_build.pk).exists())
        # The orphan configs should be deleted
        self.assertFalse(BuildConfig.objects.filter(pk=orphan_config_1.pk).exists())
        self.assertFalse(BuildConfig.objects.filter(pk=orphan_config_2.pk).exists())

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
        self.assertGreaterEqual(BuildConfig.objects.count(), 2)
        self.assertTrue(BuildConfig.objects.filter(pk=config_1.pk).exists())
        self.assertTrue(BuildConfig.objects.filter(pk=config_2.pk).exists())

        # Call the task
        remove_orphan_build_config()

        # Verify that no configs were deleted
        self.assertTrue(BuildConfig.objects.filter(pk=config_1.pk).exists())
        self.assertTrue(BuildConfig.objects.filter(pk=config_2.pk).exists())


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

            [<kbd><br />🔍 Preview build <br /></kbd>](http://my-project--1.readthedocs.build/en/1/)


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

            [<kbd><br />🔍 Preview build <br /></kbd>](http://my-project--1.readthedocs.build/en/1/)


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

            [<kbd><br />🔍 Preview build <br /></kbd>](http://my-project--1.readthedocs.build/en/1/)


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
