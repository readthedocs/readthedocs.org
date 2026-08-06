"""Test core util functions."""
import datetime
from unittest import mock

import pytest
from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_TRIGGERED,
    LATEST,
)
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import admit_project_builds, slugify, trigger_build
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.projects.models import Feature, Project
from readthedocs.subscriptions.constants import TYPE_CONCURRENT_BUILDS
from readthedocs.subscriptions.products import RTDProductFeature


@override_settings(
    RTD_DEFAULT_FEATURES=dict(
        [RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=4).to_item()]
    ),
)
class CoreUtilTests(TestCase):
    def setUp(self):
        self.project = get(
            Project, container_time_limit=None, main_language_project=None
        )
        self.version = get(Version, project=self.project)

    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_skipped_project(self, update_docs_task):
        self.project.skip = True
        self.project.save()
        result = trigger_build(
            project=self.project,
            version=self.version,
        )
        self.assertEqual(result, (None, None))
        self.assertFalse(update_docs_task.signature.called)
        self.assertFalse(update_docs_task.signature().apply_async.called)

    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_build_when_version_not_provided_default_version_exist(
        self, update_docs_task
    ):
        self.assertFalse(Version.objects.filter(slug="test-default-version").exists())

        project_1 = get(Project)
        version_1 = get(
            Version, project=project_1, slug="test-default-version", active=True
        )

        project_1.default_version = "test-default-version"
        project_1.save()

        default_version = project_1.get_default_version()
        self.assertEqual(default_version, "test-default-version")

        trigger_build(project=project_1)

        update_docs_task.signature.assert_called_with(
            args=(
                version_1.pk,
                mock.ANY,
            ),
            kwargs={
                "build_commit": None,
                "build_api_key": mock.ANY,
            },
            options=mock.ANY,
            immutable=True,
        )

    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_build_when_version_not_provided_default_version_doesnt_exist(
        self, update_docs_task
    ):
        trigger_build(project=self.project)
        default_version = self.project.get_default_version()
        version = self.project.versions.get(slug=default_version)

        self.assertEqual(version.slug, LATEST)

        update_docs_task.signature.assert_called_with(
            args=(
                version.pk,
                mock.ANY,
            ),
            kwargs={
                "build_commit": None,
                "build_api_key": mock.ANY,
            },
            options=mock.ANY,
            immutable=True,
        )

    @pytest.mark.xfail(reason="Fails while we work out Docker time limits", strict=True)
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_custom_queue(self, update_docs):
        """Use a custom queue when routing the task."""
        self.project.build_queue = "build03"
        trigger_build(project=self.project, version=self.version)
        kwargs = {"build_pk": mock.ANY, "commit": None}
        options = {
            "queue": "build03",
            "time_limit": 720,
            "soft_time_limit": 600,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @pytest.mark.xfail(reason="Fails while we work out Docker time limits", strict=True)
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_build_time_limit(self, update_docs):
        """Pass of time limit."""
        trigger_build(project=self.project, version=self.version)
        kwargs = {"build_pk": mock.ANY, "commit": None}
        options = {
            "queue": mock.ANY,
            "time_limit": 720,
            "soft_time_limit": 600,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @pytest.mark.xfail(reason="Fails while we work out Docker time limits", strict=True)
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_build_invalid_time_limit(self, update_docs):
        """Time limit as string."""
        self.project.container_time_limit = "200s"
        trigger_build(project=self.project, version=self.version)
        kwargs = {"build_pk": mock.ANY, "commit": None}
        options = {
            "queue": mock.ANY,
            "time_limit": 720,
            "soft_time_limit": 600,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk,),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )

    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_build_rounded_time_limit(self, update_docs):
        """Time limit should round down."""
        self.project.container_time_limit = 3
        trigger_build(project=self.project, version=self.version)
        options = {
            "time_limit": 3,
            "soft_time_limit": 3,
        }
        update_docs.signature.assert_called_with(
            args=(
                self.version.pk,
                mock.ANY,
            ),
            kwargs={
                "build_commit": None,
                "build_api_key": mock.ANY,
            },
            options=options,
            immutable=True,
        )

    @mock.patch("readthedocs.core.utils.app")
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_trigger_max_concurrency_reached(self, update_docs, app):
        max_concurrent_builds = 2
        for i in range(max_concurrent_builds):
            get(
                Build,
                state=BUILD_STATE_BUILDING,
                project=self.project,
                version=self.version,
                task_id=str(i),
            )
        self.project.max_concurrent_builds = max_concurrent_builds
        self.project.save()

        trigger_build(project=self.project, version=self.version)
        kwargs = {"build_commit": None, "build_api_key": mock.ANY}
        options = {
            "time_limit": settings.BUILD_TIME_LIMIT * 1.2,
            "soft_time_limit": settings.BUILD_TIME_LIMIT,
            "countdown": 5 * 60,
            "max_retries": 25,
        }
        update_docs.signature.assert_called_with(
            args=(self.version.pk, mock.ANY),
            kwargs=kwargs,
            options=options,
            immutable=True,
        )
        build = self.project.builds.first()
        notification = build.notifications.first()
        self.assertEqual(
            notification.message_id,
            BuildMaxConcurrencyError.LIMIT_REACHED,
        )
        app.control.revoke.assert_has_calls(
            [
                mock.call("1", signal="SIGINT", terminate=True),
                mock.call("0", signal="SIGINT", terminate=True),
            ]
        )

    def test_slugify(self):
        """Test additional slugify."""
        self.assertEqual(
            slugify("This is a test"),
            "this-is-a-test",
        )
        self.assertEqual(
            slugify("project_with_underscores-v.1.0"),
            "project-with-underscores-v10",
        )
        self.assertEqual(
            slugify("__project_with_trailing-underscores---"),
            "project-with-trailing-underscores",
        )
        self.assertEqual(
            slugify("project_with_underscores-v.1.0", dns_safe=False),
            "project_with_underscores-v10",
        )
        self.assertEqual(
            slugify("A title_-_with separated parts"),
            "a-title-with-separated-parts",
        )
        self.assertEqual(
            slugify("A title_-_with separated parts", dns_safe=False),
            "a-title_-_with-separated-parts",
        )


@override_settings(
    RTD_DEFAULT_FEATURES=dict(
        [RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=4).to_item()]
    ),
)
class IsolatedBuilderConcurrencyTests(TestCase):
    """Concurrency admission for the isolated-builders path."""

    def setUp(self):
        self.project = get(
            Project,
            container_time_limit=None,
            main_language_project=None,
            max_concurrent_builds=3,
        )
        feature = get(Feature, feature_id=Feature.USE_ISOLATED_BUILDER)
        feature.projects.add(self.project)
        self.version = get(Version, project=self.project)

    def _queued_build(self, minutes_ago):
        """A build waiting in ``triggered``, never dispatched."""
        build = get(
            Build,
            project=self.project,
            version=self.version,
            state=BUILD_STATE_TRIGGERED,
            task_id=None,
            dispatched_date=None,
        )
        # ``date`` is ``auto_now_add``, so set it after creation to get a
        # deterministic FIFO order for admission.
        Build.objects.filter(pk=build.pk).update(
            date=timezone.now() - datetime.timedelta(minutes=minutes_ago)
        )
        return build

    @mock.patch("readthedocs.core.utils.app.send_task")
    def test_trigger_build_isolated_path_defers_to_admission(self, send_task):
        """The isolated path leaves the build queued for the admission task."""
        task, build = trigger_build(project=self.project, version=self.version)

        assert task is None
        build.refresh_from_db()
        assert build.state == BUILD_STATE_TRIGGERED
        # Not dispatched at trigger time; the admission task owns that.
        assert build.task_id is None
        assert build.dispatched_date is None
        send_task.assert_not_called()
        # No trigger-time concurrency notification on the isolated path.
        assert build.notifications.count() == 0

    @mock.patch("readthedocs.core.utils.app.send_task")
    def test_admit_dispatches_up_to_free_slots_fifo(self, send_task):
        """Admit the oldest builds up to the free-slot count; block the rest."""
        send_task.return_value.id = "task-id"
        # 5 queued builds, ``builds[0]`` oldest.
        builds = [self._queued_build(minutes_ago=10 - i) for i in range(5)]

        admit_project_builds(self.project)

        for build in builds:
            build.refresh_from_db()

        # The 3 oldest are dispatched, no notification.
        for build in builds[:3]:
            assert build.dispatched_date is not None
            assert build.task_id == "task-id"
            assert build.notifications.count() == 0

        # The 2 newest are blocked with the concurrency notification, not sent.
        for build in builds[3:]:
            assert build.dispatched_date is None
            assert build.task_id is None
            notification = build.notifications.get()
            assert notification.message_id == BuildMaxConcurrencyError.LIMIT_REACHED

        assert send_task.call_count == 3

    @mock.patch("readthedocs.core.utils.app.send_task")
    def test_admit_does_not_overadmit_dispatched_builds(self, send_task):
        """
        Dispatched-but-not-started builds keep occupying their slot.

        Regression: a build dispatched on a previous pass (``dispatched_date``
        set) stays ``triggered`` until a builder picks it up. A later admission
        pass must keep counting it, so it must not free the slot and over-admit
        a still-queued build.
        """
        send_task.return_value.id = "task-id"
        # 3 builds already dispatched, still waiting in the broker (triggered).
        for i in range(3):
            get(
                Build,
                project=self.project,
                version=self.version,
                state=BUILD_STATE_TRIGGERED,
                task_id=str(i),
                dispatched_date=timezone.now(),
            )
        # 1 build genuinely queued.
        queued = self._queued_build(minutes_ago=1)

        admit_project_builds(self.project)

        queued.refresh_from_db()
        assert queued.dispatched_date is None
        assert queued.task_id is None
        assert (
            queued.notifications.get().message_id
            == BuildMaxConcurrencyError.LIMIT_REACHED
        )
        send_task.assert_not_called()
