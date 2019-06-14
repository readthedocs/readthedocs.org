from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL, BRANCH, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC, PRIVATE, PROTECTED
from readthedocs.projects.models import Project, HTMLFile


User = get_user_model()


class TestVersionManagerBase(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: pull/merge request Version.
        self.public_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC
        )
        self.private_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE
        )
        self.protected_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PROTECTED
        )
        self.internal_versions = Version.objects.exclude(type=EXTERNAL)


class TestInternalVersionManager(TestVersionManagerBase):

    """
    Queries using Internal Manager should only include Internal Versions.

    It will exclude EXTERNAL type Versions from the queries
    and only include BRANCH, TAG, UNKONWN type Versions.
    """

    def test_internal_version_manager_with_all(self):
        self.assertNotIn(self.public_pr_version, Version.internal.all())

    def test_internal_version_manager_with_public(self):
        self.assertNotIn(self.public_pr_version, Version.internal.public())

    def test_internal_version_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.public_pr_version,
            Version.internal.public(self.user, self.pip)
        )

    def test_internal_version_manager_with_protected(self):
        self.assertNotIn(self.protected_pr_version, Version.internal.protected())

    def test_internal_version_manager_with_private(self):
        self.assertNotIn(self.private_pr_version, Version.internal.private())

    def test_internal_version_manager_with_api(self):
        self.assertNotIn(self.public_pr_version, Version.internal.api())

    def test_internal_version_manager_with_for_project(self):
        self.assertNotIn(self.public_pr_version, Version.internal.for_project(self.pip))


class TestExternalVersionManager(TestVersionManagerBase):

    """
    Queries using External Manager should only include External Versions.

    It will only include pull/merge request Version in the queries.
    """

    def test_external_version_manager_with_all(self):
        self.assertNotIn(self.internal_versions, Version.external.all())
        self.assertIn(self.public_pr_version, Version.external.all())

    def test_external_version_manager_with_public(self):
        self.assertNotIn(self.internal_versions, Version.external.public())
        self.assertIn(self.public_pr_version, Version.external.public())

    def test_external_version_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.internal_versions,
            Version.external.public(self.user, self.pip)
        )
        self.assertIn(
            self.public_pr_version,
            Version.external.public(self.user, self.pip)
        )

    def test_external_version_manager_with_protected(self):
        self.assertNotIn(self.internal_versions, Version.external.protected())
        self.assertIn(self.protected_pr_version, Version.external.protected())

    def test_external_version_manager_with_private(self):
        self.assertNotIn(self.internal_versions, Version.external.private())
        self.assertIn(self.private_pr_version, Version.external.private())

    def test_external_version_manager_with_api(self):
        self.assertNotIn(self.internal_versions, Version.external.api())
        self.assertIn(self.public_pr_version, Version.external.api())

    def test_external_version_manager_with_for_project(self):
        self.assertNotIn(
            self.internal_versions, Version.external.for_project(self.pip)
        )
        self.assertIn(
            self.public_pr_version, Version.external.for_project(self.pip)
        )


class TestHTMLFileManager(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: PULL_REQUEST type Version.
        self.pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=PULL_REQUEST,
            privacy_level=PUBLIC
        )
        self.html_file = HTMLFile.objects.create(
            project=self.pip,
            version=self.pr_version,
            name='file.html',
            slug='file',
            path='file.html',
            md5='abcdef',
            commit='1234567890abcdef',
        )
        self.internal_html_files = HTMLFile.objects.exclude(version__type=PULL_REQUEST)

    def test_internal_html_file_manager(self):
        """
        It will exclude PULL_REQUEST type Version html files from the queries
        and only include BRANCH, TAG, UNKONWN type Version files.
        """
        self.assertNotIn(self.html_file, HTMLFile.objects.internal())

    def test_external_html_file_manager(self):
        """
        It will only include PULL_REQUEST type Version html files in the queries.
        """
        self.assertNotIn(self.internal_html_files, HTMLFile.objects.external())
        self.assertIn(self.html_file, HTMLFile.objects.external())
