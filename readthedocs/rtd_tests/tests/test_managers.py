from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import PULL_REQUEST, BRANCH, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PUBLIC, PRIVATE, PROTECTED
from readthedocs.projects.models import Project


User = get_user_model()


class TestVersionManagerBase(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: PULL_REQUEST type Version.
        self.public_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=PULL_REQUEST,
            privacy_level=PUBLIC
        )
        self.private_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=PULL_REQUEST,
            privacy_level=PRIVATE
        )
        self.protected_pr_version = get(
            Version,
            project=self.pip,
            active=True,
            type=PULL_REQUEST,
            privacy_level=PROTECTED
        )
        self.internal_versions = Version.objects.exclude(type=PULL_REQUEST)


class TestInternalVersionManager(TestVersionManagerBase):

    """
    Queries using Internal Manager should only include Internal Versions.

    It will exclude PULL_REQUEST type Versions from the queries
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

    It will only include PULL_REQUEST type Versions in the queries.
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
