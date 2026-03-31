from unittest import mock

import django_dynamic_fixture as fixture
from django.test import TestCase

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.models import Version
from readthedocs.core.views.hooks import VersionInfo
from readthedocs.core.views.hooks import build_versions_from_names
from readthedocs.projects.constants import SINGLE_VERSION_WITHOUT_TRANSLATIONS
from readthedocs.projects.models import Project


class BuildVersionsFromNamesTests(TestCase):
    @mock.patch("readthedocs.core.views.hooks.trigger_build")
    def test_skips_non_default_version_on_single_version_project(self, trigger_build):
        project = fixture.get(
            Project,
            versioning_scheme=SINGLE_VERSION_WITHOUT_TRANSLATIONS,
            default_version="latest",
            main_language_project=None,
        )
        version = fixture.get(
            Version,
            project=project,
            slug="feature-branch",
            verbose_name="feature-branch",
            type=BRANCH,
            active=True,
            machine=False,
        )
        trigger_build.return_value = (None, None)

        to_build, not_building = build_versions_from_names(
            project,
            [VersionInfo(name=version.verbose_name, type=version.type)],
        )

        self.assertEqual(to_build, set())
        self.assertEqual(not_building, {version.slug})
        trigger_build.assert_called_once_with(
            project=project,
            version=version,
            from_webhook=True,
        )
