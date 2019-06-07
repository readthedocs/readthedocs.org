from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import PULL_REQUEST, BRANCH, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project


class VersionMixin:

    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: PULL_REQUEST type Version.
        self.pr_version = get(
            Version,
            identifier='9F86D081884C7D659A2FEAA0C55AD015A',
            verbose_name='pr-version',
            slug='9999',
            project=self.pip,
            active=True,
            type=PULL_REQUEST
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


class TestVersionModel(VersionMixin, TestCase):

    def test_vcs_url_for_pr_version(self):
        expected_url = f'https://github.com/pypa/pip/pull/{self.pr_version.slug}/'
        self.assertEqual(self.pr_version.vcs_url, expected_url)

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

    def test_commit_name_for_pr_version(self):
        self.assertEqual(self.pr_version.commit_name, self.pr_version.identifier)
