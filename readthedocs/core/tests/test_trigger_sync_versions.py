from unittest import mock

import django_dynamic_fixture as fixture
from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.core.views.hooks import trigger_sync_versions
from readthedocs.projects.models import Feature
from readthedocs.projects.models import Project


@mock.patch("readthedocs.core.views.hooks.app")
@mock.patch("readthedocs.core.views.hooks.sync_repository_task")
class TestTriggerSyncVersions(TestCase):
    def setUp(self):
        cache.clear()
        self.project = fixture.get(
            Project,
            slug="pip",
            repo="https://github.com/readthedocs/pip",
        )
        self.version = self.project.versions.get(slug=LATEST)

    def _enable_build_isolated(self, *projects):
        # ``feature_id`` is unique, so a second project joins the same Feature.
        feature, _ = Feature.objects.get_or_create(feature_id=Feature.USE_BUILD_ISOLATED)
        feature.projects.add(*(projects or [self.project]))

    def test_legacy_projects_use_the_celery_task(self, sync_repository_task, app):
        assert trigger_sync_versions(self.project) == self.version.slug

        sync_repository_task.apply_async.assert_called_once()
        app.send_task.assert_not_called()

    @override_settings(RTD_SYNC_REPOSITORY_ISOLATED_TASK_NAME="worker.tasks.sync_repository")
    def test_isolated_projects_dispatch_to_the_worker(self, sync_repository_task, app):
        self._enable_build_isolated()

        assert trigger_sync_versions(self.project) == self.version.slug

        sync_repository_task.apply_async.assert_not_called()
        args, kwargs = app.send_task.call_args
        assert args[0] == "worker.tasks.sync_repository"
        assert kwargs["queue"] == "build:isolated"
        assert kwargs["kwargs"]["project_pk"] == self.project.pk
        assert kwargs["kwargs"]["build_api_key"]
        assert kwargs["kwargs"]["environment"]["RTD_PRODUCTION_DOMAIN"]

    def test_a_burst_dispatches_a_single_sync(self, sync_repository_task, app):
        # A tag push sends one webhook per ref; they all ask for the same sync.
        self._enable_build_isolated()

        slugs = [trigger_sync_versions(self.project) for _ in range(5)]

        assert slugs == [self.version.slug] * 5
        assert app.send_task.call_count == 1

    def test_the_debounce_is_per_project(self, sync_repository_task, app):
        self._enable_build_isolated()
        other = fixture.get(Project, slug="other", repo="https://github.com/readthedocs/other")
        self._enable_build_isolated(other)

        trigger_sync_versions(self.project)
        trigger_sync_versions(other)

        assert app.send_task.call_count == 2

    def test_skip_sync_versions_is_honored(self, sync_repository_task, app):
        self._enable_build_isolated()
        skip, _ = Feature.objects.get_or_create(feature_id=Feature.SKIP_SYNC_VERSIONS)
        skip.projects.add(self.project)

        assert trigger_sync_versions(self.project) is None
        app.send_task.assert_not_called()

    def test_a_project_without_a_latest_version_is_skipped(self, sync_repository_task, app):
        self._enable_build_isolated()
        Version.objects.filter(project=self.project).delete()

        assert trigger_sync_versions(self.project) is None
        app.send_task.assert_not_called()
