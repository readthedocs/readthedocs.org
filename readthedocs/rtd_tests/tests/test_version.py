from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH, EXTERNAL, LATEST, STABLE, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class VersionMixin:
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username="eric", password="test")
        self.pip = Project.objects.get(slug="pip")
        # Create a External Version. ie: pull/merge request Version.
        self.external_version = get(
            Version,
            identifier="9F86D081884C7D659A2FEAA0C55AD015A",
            verbose_name="9999",
            slug="pr-9999",
            project=self.pip,
            active=True,
            type=EXTERNAL,
        )
        self.branch_version = get(
            Version,
            identifier="origin/stable",
            verbose_name="stable",
            slug="stable",
            project=self.pip,
            active=True,
            type=BRANCH,
            machine=True,
        )
        self.tag_version = get(
            Version,
            identifier="master",
            verbose_name="latest",
            slug="latest",
            project=self.pip,
            active=True,
            type=TAG,
            machine=True,
        )

        self.subproject = get(Project, slug="subproject", language="en")
        self.translation_subproject = get(
            Project,
            language="es",
            slug="translation-subproject",
            main_language_project=self.subproject,
        )
        self.pip.add_subproject(self.subproject)


class TestVersionModel(VersionMixin, TestCase):
    def test_vcs_url_for_external_version_github(self):
        self.pip.repo = "https://github.com/pypa/pip"
        self.pip.save()

        expected_url = (
            f"https://github.com/pypa/pip/pull/{self.external_version.verbose_name}"
        )
        self.assertEqual(self.external_version.vcs_url, expected_url)

    def test_vcs_url_for_external_version_gitlab(self):
        self.pip.repo = "https://gitlab.com/pypa/pip"
        self.pip.save()

        expected_url = f"https://gitlab.com/pypa/pip/merge_requests/{self.external_version.verbose_name}"
        self.assertEqual(self.external_version.vcs_url, expected_url)

    def test_vcs_url_for_latest_version(self):
        slug = self.pip.default_branch or self.pip.vcs_class().fallback_branch
        expected_url = f"https://github.com/pypa/pip/tree/{slug}/"
        self.assertEqual(self.tag_version.vcs_url, expected_url)

    def test_vcs_url_for_manual_latest_version(self):
        latest = self.pip.versions.get(slug=LATEST)
        latest.machine = False
        latest.save()
        assert "https://github.com/pypa/pip/tree/latest/" == latest.vcs_url

    def test_vcs_url_for_stable_version(self):
        self.pip.update_stable_version()
        self.branch_version.refresh_from_db()
        expected_url = f"https://github.com/pypa/pip/tree/{self.branch_version.ref}/"
        self.assertEqual(self.branch_version.vcs_url, expected_url)

    def test_vcs_url_for_manual_stable_version(self):
        stable = self.pip.versions.get(slug=STABLE)
        stable.machine = False
        stable.save()
        assert "https://github.com/pypa/pip/tree/stable/" == stable.vcs_url

    def test_git_identifier_for_stable_version(self):
        self.assertEqual(self.branch_version.git_identifier, "stable")

    def test_stable_version_original_version_query_is_shared(self):
        get(Version, project=self.pip, slug="9.0", verbose_name="9.0", identifier="sha-9.0", type=TAG)
        get(Version, project=self.pip, slug="9.1", verbose_name="9.1", identifier="sha-9.0", type=TAG)
        # Not synced to stable yet, ``ref`` follows what stable points to.
        get(Version, project=self.pip, slug="10.0", verbose_name="10.0", identifier="sha-10.0", type=TAG)
        stable = self.pip.versions.get(slug=STABLE)
        stable.identifier = "sha-9.0"
        stable.type = TAG
        stable.save()

        stable = self.pip.versions.select_related("project").get(slug=STABLE)
        # ``ref``, ``git_identifier`` and ``vcs_url`` share a single query,
        # filtered by identifier instead of reading every version of the project.
        with self.assertNumQueries(1):
            assert stable.ref == "9.1"
            assert stable.git_identifier == "9.1"
            assert stable.vcs_url == "https://github.com/pypa/pip/tree/9.1/"
        assert self.pip.get_original_stable_version().slug == "9.1"

    def test_ref_for_manual_stable_version(self):
        stable = self.pip.versions.get(slug=STABLE)
        stable.machine = False
        stable.save()
        assert stable.ref is None
        assert stable.original_stable_version is None
        assert self.pip.get_original_stable_version() is None

    def test_ref_for_non_stable_version(self):
        assert self.tag_version.ref is None
        assert self.external_version.ref is None

    def test_original_latest_version(self):
        main = get(Version, project=self.pip, slug="main", verbose_name="main", identifier="main", type=BRANCH)
        latest = self.pip.versions.get(slug=LATEST)
        latest.identifier = "main"
        latest.save()
        assert latest.original_latest_version == main
        assert self.pip.get_original_latest_version() == main

        latest.machine = False
        latest.save()
        latest = self.pip.versions.get(slug=LATEST)
        assert latest.original_latest_version is None
        assert self.pip.get_original_latest_version() is None

    def test_git_identifier_for_latest_version(self):
        self.assertEqual(self.tag_version.git_identifier, "master")

    def test_git_identifier_for_external_version(self):
        self.assertEqual(
            self.external_version.git_identifier, self.external_version.verbose_name
        )

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_get_downloads(self):
        version = self.branch_version
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            "epub": "//pip.readthedocs.io/_/downloads/en/stable/epub/",
            "pdf": "//pip.readthedocs.io/_/downloads/en/stable/pdf/",
        }
        self.assertDictEqual(version.get_downloads(), expected)

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_get_downloads_subproject(self):
        version = self.subproject.versions.get(slug=LATEST)
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            "epub": "//pip.readthedocs.io/_/downloads/subproject/en/latest/epub/",
            "pdf": "//pip.readthedocs.io/_/downloads/subproject/en/latest/pdf/",
        }
        self.assertDictEqual(version.get_downloads(), expected)

    @override_settings(
        PRODUCTION_DOMAIN="readthedocs.org",
        PUBLIC_DOMAIN="readthedocs.io",
    )
    def test_get_downloads_translation_subproject(self):
        version = self.translation_subproject.versions.get(slug=LATEST)
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            "epub": "//pip.readthedocs.io/_/downloads/subproject/es/latest/epub/",
            "pdf": "//pip.readthedocs.io/_/downloads/subproject/es/latest/pdf/",
        }
        self.assertDictEqual(version.get_downloads(), expected)
