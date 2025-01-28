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
