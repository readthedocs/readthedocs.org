from unittest import mock

import django_dynamic_fixture as fixture
import pytest

from readthedocs.builds.constants import (
    BUILD_STATE_BUILDING,
    BUILD_STATE_CANCELLED,
    BUILD_STATE_CLONING,
    BUILD_STATE_FINISHED,
    BUILD_STATE_INSTALLING,
    BUILD_STATE_TRIGGERED,
    BUILD_STATE_UPLOADING,
)
from readthedocs.builds.models import Build, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestCancelOldBuilds:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.project = fixture.get(Project)
        self.version = fixture.get(Version, project=self.project)

    @pytest.mark.parametrize(
        "state",
        [
            BUILD_STATE_TRIGGERED,
            BUILD_STATE_CLONING,
            BUILD_STATE_INSTALLING,
            BUILD_STATE_BUILDING,
            BUILD_STATE_UPLOADING,
        ],
    )
    @mock.patch("readthedocs.core.utils.cancel_build")
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_cancel_old_running_build(self, update_docs_task, cancel_build, state):
        # Create a running build
        build = fixture.get(
            Build, project=self.project, version=self.version, state=state
        )

        builds_count_before = Build.objects.count()

        # Trigger a new build for the same project/version
        result = trigger_build(
            project=self.project,
            version=self.version,
        )

        triggered_build = Build.objects.first()
        builds_count_after = Build.objects.count()

        cancel_build.assert_called_once_with(build)
        assert result == (mock.ANY, triggered_build)
        assert builds_count_before == builds_count_after - 1
        assert update_docs_task.signature.called
        assert update_docs_task.signature().apply_async.called

    @pytest.mark.parametrize(
        "state",
        [
            BUILD_STATE_CANCELLED,
            BUILD_STATE_FINISHED,
        ],
    )
    @mock.patch("readthedocs.core.utils.cancel_build")
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_not_cancel_old_finished_build(self, update_docs_task, cancel_build, state):
        # Create a running build
        build = fixture.get(
            Build, project=self.project, version=self.version, state=state
        )

        builds_count_before = Build.objects.count()

        # Trigger a new build for the same project/version
        result = trigger_build(
            project=self.project,
            version=self.version,
        )

        triggered_build = Build.objects.first()
        builds_count_after = Build.objects.count()

        cancel_build.assert_not_called()
        assert result == (mock.ANY, triggered_build)
        assert builds_count_before == builds_count_after - 1
        assert update_docs_task.signature.called
        assert update_docs_task.signature().apply_async.called

    @mock.patch("readthedocs.core.utils.cancel_build")
    @mock.patch("readthedocs.projects.tasks.builds.update_docs_task")
    def test_update_latest_build_on_trigger(self, update_docs_task, cancel_build):
        assert self.project.builds.count() == 0
        assert self.project.latest_build is None
        _, build = trigger_build(
            project=self.project,
            version=self.version,
        )

        self.project.refresh_from_db()
        assert self.project.builds.count() == 1
        assert self.project.latest_build == build

        _, build = trigger_build(
            project=self.project,
            version=self.version,
        )
        self.project.refresh_from_db()
        assert self.project.builds.count() == 2
        assert self.project.latest_build == build
