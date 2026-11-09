import datetime
from unittest import mock

import django_dynamic_fixture as fixture
import pytest

from readthedocs.api.v2.client import setup_api
from readthedocs.builds.models import Build
from readthedocs.doc_builder.environments import DockerBuildEnvironment
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestDockerBuildEnvironmentNew:
    @pytest.fixture(autouse=True)
    def setup(self, requests_mock):
        # Save the reference to query it from inside the test
        self.requests_mock = requests_mock

        self.project = fixture.get(
            Project,
            slug="project",
        )
        self.version = self.project.versions.get(slug="latest")
        self.build = fixture.get(
            Build,
            version=self.version,
            commit="a1b2c3",
        )

        self.environment = DockerBuildEnvironment(
            project=self.project,
            version=self.version,
            build={"id": self.build.pk},
            api_client=setup_api("1234"),
        )

    def test_container_id(self):
        assert (
            self.environment.container_id
            == f"build-{self.build.pk}-project-{self.project.pk}-{self.project.slug}"
        )

    def test_container_time_limit(self, settings):
        assert self.environment.container_time_limit == settings.BUILD_TIME_LIMIT

    @mock.patch("django.utils.timezone.now")
    def test_container_time_limit_counts_from_task_start(self, now, settings):
        start_time = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
        now.return_value = start_time + datetime.timedelta(seconds=100)
        environment = DockerBuildEnvironment(
            project=self.project,
            version=self.version,
            build={"id": self.build.pk},
            api_client=setup_api("1234"),
            start_time=start_time,
        )
        assert environment.container_time_limit == settings.BUILD_TIME_LIMIT - 100
