import pytest

import django_dynamic_fixture as fixture
from django.conf import settings

from readthedocs.builds.querysets import BuildQuerySet
from readthedocs.builds.models import Build, Version
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project, Feature


@pytest.mark.django_db
class TestBuildQuerySet:

    def test_concurrent_builds(self):
        project = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        for state in ('triggered', 'building', 'cloning', 'finished'):
            fixture.get(
                Build,
                project=project,
                state=state,
            )
        assert (False, 2, 4) == Build.objects.concurrent(project)
        for state in ('building', 'cloning'):
            fixture.get(
                Build,
                project=project,
                state=state,
            )
        assert (True, 4, 4) == Build.objects.concurrent(project)

    def test_concurrent_builds_project_limited(self):
        project = fixture.get(
            Project,
            max_concurrent_builds=2,
            main_language_project=None,
        )
        for state in ('triggered', 'building', 'cloning', 'finished'):
            fixture.get(
                Build,
                project=project,
                state=state,
            )
        assert (True, 2, 2) == Build.objects.concurrent(project)

    def test_concurrent_builds_translations(self):
        project = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        translation = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=project,
        )
        for state in ('triggered', 'building', 'cloning', 'finished'):
            fixture.get(
                Build,
                project=project,
                state=state,
            )
        assert (False, 2, 4) == Build.objects.concurrent(translation)

        for state in ('building', 'cloning'):
            fixture.get(
                Build,
                project=translation,
                state=state,
            )
        assert (True, 4, 4) == Build.objects.concurrent(translation)
        assert (True, 4, 4) == Build.objects.concurrent(project)

    def test_concurrent_builds_organization(self):
        organization = fixture.get(
            Organization,
            max_concurrent_builds=None,
        )

        for _ in range(2):
            project = fixture.get(
                Project,
                max_concurrent_builds=None,
                main_language_project=None,
            )
            organization.projects.add(project)

        for project in organization.projects.all():
            for state in ('triggered', 'building', 'cloning', 'finished'):
                fixture.get(
                    Build,
                    project=project,
                    state=state,
                )

        project = organization.projects.first()
        assert (True, 4, 4) == Build.objects.concurrent(project)
        for state in ('building', 'cloning'):
            fixture.get(
                Build,
                project=project,
                state=state,
            )
        assert (True, 6, 4) == Build.objects.concurrent(project)

    def test_concurrent_builds_organization_limited(self):
        organization = fixture.get(
            Organization,
            max_concurrent_builds=10,
        )
        project_with_builds = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        project_without_builds = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        organization.projects.add(project_with_builds)
        organization.projects.add(project_without_builds)
        for state in ('triggered', 'building', 'cloning', 'finished'):
            fixture.get(
                Build,
                project=project_with_builds,
                state=state,
            )
        # Calling it with ``project_without_builds`` should count the builds
        # from ``project_with_builds`` as well
        assert (False, 2, 10) == Build.objects.concurrent(project_without_builds)

    def test_concurrent_builds_organization_and_project_limited(self):
        organization = fixture.get(
            Organization,
            max_concurrent_builds=10,
        )
        project_limited = fixture.get(
            Project,
            max_concurrent_builds=2,
            main_language_project=None,
        )
        project_not_limited = fixture.get(
            Project,
            max_concurrent_builds=None,
            main_language_project=None,
        )
        organization.projects.add(project_limited)
        organization.projects.add(project_not_limited)
        for state in ('triggered', 'building', 'cloning', 'finished'):
            fixture.get(
                Build,
                project=project_limited,
                state=state,
            )
        assert (True, 2, 2) == Build.objects.concurrent(project_limited)
        assert (False, 2, 10) == Build.objects.concurrent(project_not_limited)
