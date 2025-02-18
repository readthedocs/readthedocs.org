import django_dynamic_fixture as fixture
import pytest

from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project
from readthedocs.projects.version_handling import (
    sort_versions_calver,
    sort_versions_custom_pattern,
    sort_versions_python_packaging,
)


@pytest.mark.django_db(databases="__all__")
class TestVersionHandling:
    @pytest.fixture(autouse=True)
    def setup(self, requests_mock):
        # Save the reference to query it from inside the test
        self.requests_mock = requests_mock

        self.project = fixture.get(Project, slug="project")
        self.version = self.project.versions.get(slug="latest")
        self.build = fixture.get(
            Build,
            version=self.version,
            commit="a1b2c3",
        )

    def test_sort_versions_python_packaging(self):
        slugs = [
            "v1.0",
            "1.1",
            "invalid",
            "2.5.3",
            "1.1.0",
            "another-invalid",
        ]

        expected = [
            # `latest` and `stable` are at the beginning
            "latest",
            "2.5.3",
            "1.1.0",
            "1.1",
            "v1.0",
            # Invalid versions are at the end sorted alphabetically.
            "invalid",
            "another-invalid",
        ]

        for slug in slugs:
            fixture.get(
                Version,
                slug=slug,
                project=self.project,
            )

        sorted_versions = sort_versions_python_packaging(
            self.project.versions.all(),
            latest_stable_at_beginning=True,
        )
        assert expected == [version.slug for version in sorted_versions]

    def test_sort_versions_python_packaging_latest_stable_not_at_beginning(self):
        slugs = [
            "v1.0",
            "1.1",
            "invalid",
            "2.5.3",
            "1.1.0",
            "another-invalid",
        ]

        expected = [
            "2.5.3",
            "1.1.0",
            "1.1",
            "v1.0",
            # Invalid versions are at the end sorted alphabetically.
            "latest",
            "invalid",
            "another-invalid",
        ]

        for slug in slugs:
            fixture.get(
                Version,
                slug=slug,
                project=self.project,
            )

        sorted_versions = sort_versions_python_packaging(
            self.project.versions.all(),
            latest_stable_at_beginning=False,
        )
        assert expected == [version.slug for version in sorted_versions]

    def test_sort_versions_calver(self):
        slugs = [
            "2022.01.22",
            "2023.04.22",
            "2021.01.22",
            "2022.05.02",
            # invalid ones
            "2001.16.32",
            "2001.02.2",
            "2001-02-27",
            "1.1",
            "invalid",
            "2.5.3",
            "1.1.0",
            "another-invalid",
        ]

        expected = [
            # `latest` and `stable` are at the beginning
            "latest",
            "stable",
            "2023.04.22",
            "2022.05.02",
            "2022.01.22",
            "2021.01.22",
            # invalid ones (alphabetically)
            "invalid",
            "another-invalid",
            "2001.16.32",
            "2001.02.2",
            "2001-02-27",
            "2.5.3",
            "1.1.0",
            "1.1",
        ]

        for slug in slugs:
            fixture.get(
                Version,
                slug=slug,
                project=self.project,
            )

        fixture.get(
            Version,
            slug="stable",
            machine=True,
            project=self.project,
        )

        sorted_versions = sort_versions_calver(
            self.project.versions.all(),
            latest_stable_at_beginning=True,
        )

        assert expected == [version.slug for version in sorted_versions]

    def test_sort_versions_custom_pattern(self):
        slugs = [
            "v1.0",
            "v1.1",
            "v2.3",
            # invalid ones
            "v1.1.0",
            "v2.3rc1",
            "invalid",
            "2.5.3",
            "2022.01.22",
            "1.1",
            "another-invalid",
        ]

        expected = [
            # `latest` and `stable` are at the beginning
            "latest",
            "stable",
            "v2.3",
            "v1.1",
            "v1.0",
            # invalid ones (alphabetically)
            "v2.3rc1",
            "v1.1.0",
            "invalid",
            "another-invalid",
            "2022.01.22",
            "2.5.3",
            "1.1",
        ]

        for slug in slugs:
            fixture.get(
                Version,
                slug=slug,
                project=self.project,
            )

        fixture.get(
            Version,
            slug="stable",
            machine=True,
            project=self.project,
        )

        sorted_versions = sort_versions_custom_pattern(
            self.project.versions.all(),
            raw_pattern="vMAJOR.MINOR",
            latest_stable_at_beginning=True,
        )

        assert expected == [version.slug for version in sorted_versions]
