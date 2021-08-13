from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH, EXTERNAL, LATEST, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class VersionMixin:

    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: pull/merge request Version.
        self.external_version = get(
            Version,
            identifier='9F86D081884C7D659A2FEAA0C55AD015A',
            verbose_name='9999',
            slug='pr-9999',
            project=self.pip,
            active=True,
            type=EXTERNAL
        )
        self.branch_version = get(
            Version,
            identifier='origin/stable',
            verbose_name='stable',
            slug='stable',
            project=self.pip,
            active=True,
            type=BRANCH
        )
        self.tag_version = get(
            Version,
            identifier='origin/master',
            verbose_name='latest',
            slug='latest',
            project=self.pip,
            active=True,
            type=TAG
        )

        self.subproject = get(Project, slug='subproject', language='en')
        self.translation_subproject = get(
            Project,
            language='es',
            slug='translation-subproject',
            main_language_project=self.subproject,
        )
        self.pip.add_subproject(self.subproject)


class TestVersionModel(VersionMixin, TestCase):

    def test_vcs_url_for_external_version_github(self):
        self.pip.repo = 'https://github.com/pypa/pip'
        self.pip.save()

        expected_url = f'https://github.com/pypa/pip/pull/{self.external_version.verbose_name}'
        self.assertEqual(self.external_version.vcs_url, expected_url)

    def test_vcs_url_for_external_version_gitlab(self):
        self.pip.repo = 'https://gitlab.com/pypa/pip'
        self.pip.save()

        expected_url = f'https://gitlab.com/pypa/pip/merge_requests/{self.external_version.verbose_name}'
        self.assertEqual(self.external_version.vcs_url, expected_url)

    def test_vcs_url_for_latest_version(self):
        slug = self.pip.default_branch or self.pip.vcs_repo().fallback_branch
        expected_url = f'https://github.com/pypa/pip/tree/{slug}/'
        self.assertEqual(self.tag_version.vcs_url, expected_url)

    def test_vcs_url_for_stable_version(self):
        expected_url = f'https://github.com/pypa/pip/tree/{self.branch_version.ref}/'
        self.assertEqual(self.branch_version.vcs_url, expected_url)

    def test_commit_name_for_stable_version(self):
        self.assertEqual(self.branch_version.commit_name, 'stable')

    def test_commit_name_for_latest_version(self):
        self.assertEqual(self.tag_version.commit_name, 'master')

    def test_commit_name_for_external_version(self):
        self.assertEqual(self.external_version.commit_name, self.external_version.identifier)

    def test_version_does_not_support_wipe(self):
        self.assertFalse(self.external_version.supports_wipe)

    def test_version_supports_wipe(self):
        self.assertTrue(self.branch_version.supports_wipe)

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_get_downloads(self):
        version = self.branch_version
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            'epub': '//pip.readthedocs.io/_/downloads/en/stable/epub/',
            'pdf': '//pip.readthedocs.io/_/downloads/en/stable/pdf/',
        }
        self.assertDictEqual(version.get_downloads(), expected)

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_get_downloads_subproject(self):
        version = self.subproject.versions.get(slug=LATEST)
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            'epub': '//pip.readthedocs.io/_/downloads/subproject/en/latest/epub/',
            'pdf': '//pip.readthedocs.io/_/downloads/subproject/en/latest/pdf/',
        }
        self.assertDictEqual(version.get_downloads(), expected)

    @override_settings(
        PRODUCTION_DOMAIN='readthedocs.org',
        PUBLIC_DOMAIN='readthedocs.io',
        USE_SUBDOMAIN=True,
    )
    def test_get_downloads_translation_subproject(self):
        version = self.translation_subproject.versions.get(slug=LATEST)
        self.assertDictEqual(version.get_downloads(), {})
        version.has_pdf = True
        version.has_epub = True
        version.save()

        expected = {
            'epub': '//pip.readthedocs.io/_/downloads/subproject/es/latest/epub/',
            'pdf': '//pip.readthedocs.io/_/downloads/subproject/es/latest/pdf/',
        }
        self.assertDictEqual(version.get_downloads(), expected)
