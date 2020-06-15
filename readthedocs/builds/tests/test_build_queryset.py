import pytest

import django_dynamic_fixture as fixture
from django.conf import settings

from readthedocs.builds.querysets import BuildQuerySet
from readthedocs.builds.models import Build, Version
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
