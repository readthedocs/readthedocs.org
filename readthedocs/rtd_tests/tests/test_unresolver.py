import django_dynamic_fixture as fixture
import pytest
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.core.unresolver import unresolve
from readthedocs.projects.models import Domain, Project
from readthedocs.rtd_tests.tests.test_resolver import ResolverBase


@override_settings(
    PUBLIC_DOMAIN='readthedocs.io',
    RTD_EXTERNAL_VERSION_DOMAIN='dev.readthedocs.build',
)
@pytest.mark.proxito
class UnResolverTests(ResolverBase):

    def test_unresolver(self):
        parts = unresolve(
            "https://pip.readthedocs.io/en/latest/foo.html?search=api#fragment"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/foo.html")
        self.assertEqual(parts.parsed_url.fragment, "fragment")
        self.assertEqual(parts.parsed_url.query, "search=api")

    def test_filename_wihtout_index(self):
        parts = unresolve(
            "https://pip.readthedocs.io/en/latest/file/", append_indexhtml=False
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/file/")

    def test_no_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_file_with_trailing_slash(self):
        parts = unresolve("https://pip.readthedocs.io/en/latest/foo/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/foo/index.html")

    def test_path_no_version(self):
        urls = [
            "https://pip.readthedocs.io/en",
            "https://pip.readthedocs.io/en/",
        ]
        for url in urls:
            parts = unresolve(url)
            self.assertEqual(parts.parent_project, self.pip)
            self.assertEqual(parts.project, self.pip)
            self.assertEqual(parts.version, None)
            self.assertEqual(parts.filename, None)

    def test_unresolver_subproject(self):
        parts = unresolve("https://pip.readthedocs.io/projects/sub/ja/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_with_translation(self):
        subproject_translation = get(
            Project,
            main_language_project=self.subproject,
            language="en",
            slug="subproject-translation",
        )
        version = subproject_translation.versions.first()
        parts = unresolve("https://pip.readthedocs.io/projects/sub/en/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, subproject_translation)
        self.assertEqual(parts.version, version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_single_version(self):
        self.subproject.single_version = True
        self.subproject.save()
        parts = unresolve("https://pip.readthedocs.io/projects/sub/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_subproject_alias(self):
        relation = self.pip.subprojects.first()
        relation.alias = "sub_alias"
        relation.save()
        parts = unresolve("https://pip.readthedocs.io/projects/sub_alias/ja/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_subproject_invalid_version(self):
        parts = unresolve("https://pip.readthedocs.io/projects/sub/ja/nothing/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_unresolve_subproject_invalid_translation(self):
        parts = unresolve("https://pip.readthedocs.io/projects/sub/es/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_unresolver_translation(self):
        parts = unresolve("https://pip.readthedocs.io/ja/latest/foo.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.translation)
        self.assertEqual(parts.version, self.translation_version)
        self.assertEqual(parts.filename, "/foo.html")

    def test_unresolve_no_existing_translation(self):
        parts = unresolve("https://pip.readthedocs.io/es/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_unresolver_custom_domain(self):
        self.domain = fixture.get(
            Domain,
            domain='docs.foobar.com',
            project=self.pip,
            canonical=True,
        )
        parts = unresolve("https://docs.foobar.com/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_single_version(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve("https://pip.readthedocs.io/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolve_single_version_translation_like_path(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve("https://pip.readthedocs.io/en/latest/index.html")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/en/latest/index.html")

    def test_unresolve_single_version_subproject_like_path(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve(
            "https://pip.readthedocs.io/projects/other/en/latest/index.html"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, self.version)
        self.assertEqual(parts.filename, "/projects/other/en/latest/index.html")

    def test_unresolve_single_version_subproject(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve(
            "https://pip.readthedocs.io/projects/sub/ja/latest/index.html"
        )
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.subproject)
        self.assertEqual(parts.version, self.subproject_version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unresolver_external_version(self):
        version = get(
            Version,
            project=self.pip,
            type=EXTERNAL,
            slug="10",
            active=True,
        )
        parts = unresolve("https://pip--10.dev.readthedocs.build/en/10/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, version)
        self.assertEqual(parts.filename, "/index.html")

    def test_external_version_single_version_project(self):
        self.pip.single_version = True
        self.pip.save()
        version = get(
            Version,
            project=self.pip,
            type=EXTERNAL,
            slug="10",
            active=True,
        )
        parts = unresolve("https://pip--10.dev.readthedocs.build/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, version)
        self.assertEqual(parts.filename, "/index.html")

    def test_unexisting_external_version_single_version_project(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve("https://pip--10.dev.readthedocs.build/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_non_external_version_single_version_project(self):
        self.pip.single_version = True
        self.pip.save()
        parts = unresolve("https://pip--latest.dev.readthedocs.build/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_unresolve_external_version_no_existing_version(self):
        parts = unresolve("https://pip--10.dev.readthedocs.build/en/10/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_external_version_not_matching_final_version(self):
        parts = unresolve("https://pip--10.dev.readthedocs.build/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_normal_version_in_external_version_subdomain(self):
        parts = unresolve("https://pip--latest.dev.readthedocs.build/en/latest/")
        self.assertEqual(parts.parent_project, self.pip)
        self.assertEqual(parts.project, self.pip)
        self.assertEqual(parts.version, None)
        self.assertEqual(parts.filename, None)

    def test_malformed_external_version(self):
        parts = unresolve("https://pip-latest.dev.readthedocs.build/en/latest/")
        self.assertEqual(parts, None)

    def test_unresolver_unknown_host(self):
        parts = unresolve("https://random.stuff.com/en/latest/")
        self.assertEqual(parts, None)
