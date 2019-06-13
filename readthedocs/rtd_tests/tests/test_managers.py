from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

<<<<<<< HEAD
from readthedocs.builds.constants import EXTERNAL, BRANCH, TAG
=======
from readthedocs.builds.constants import PULL_REQUEST, BRANCH, TAG
>>>>>>> build manager tests added
from readthedocs.builds.models import Version, Build
from readthedocs.projects.constants import PUBLIC, PRIVATE, PROTECTED
from readthedocs.projects.models import Project


User = get_user_model()


class TestVersionManagerBase(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: pull/merge request Version.
        self.public_external_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC
        )
        self.private_external_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE
        )
        self.protected_external_version = get(
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
        self.assertNotIn(self.public_external_version, Version.internal.all())

    def test_internal_version_manager_with_public(self):
        self.assertNotIn(self.public_external_version, Version.internal.public())

    def test_internal_version_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.public_external_version,
            Version.internal.public(self.user, self.pip)
        )

    def test_internal_version_manager_with_protected(self):
        self.assertNotIn(self.protected_external_version, Version.internal.protected())

    def test_internal_version_manager_with_private(self):
        self.assertNotIn(self.private_external_version, Version.internal.private())

    def test_internal_version_manager_with_api(self):
        self.assertNotIn(self.public_external_version, Version.internal.api())

    def test_internal_version_manager_with_for_project(self):
        self.assertNotIn(self.public_external_version, Version.internal.for_project(self.pip))


class TestExternalVersionManager(TestVersionManagerBase):

    """
    Queries using External Manager should only include External Versions.

    It will only include pull/merge request Version in the queries.
    """

    def test_external_version_manager_with_all(self):
        self.assertNotIn(self.internal_versions, Version.external.all())
        self.assertIn(self.public_external_version, Version.external.all())

    def test_external_version_manager_with_public(self):
        self.assertNotIn(self.internal_versions, Version.external.public())
        self.assertIn(self.public_external_version, Version.external.public())

    def test_external_version_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.internal_versions,
            Version.external.public(self.user, self.pip)
        )
        self.assertIn(
            self.public_external_version,
            Version.external.public(self.user, self.pip)
        )

    def test_external_version_manager_with_protected(self):
        self.assertNotIn(self.internal_versions, Version.external.protected())
        self.assertIn(self.protected_external_version, Version.external.protected())

    def test_external_version_manager_with_private(self):
        self.assertNotIn(self.internal_versions, Version.external.private())
        self.assertIn(self.private_external_version, Version.external.private())

    def test_external_version_manager_with_api(self):
        self.assertNotIn(self.internal_versions, Version.external.api())
        self.assertIn(self.public_external_version, Version.external.api())

    def test_external_version_manager_with_for_project(self):
        self.assertNotIn(
            self.internal_versions, Version.external.for_project(self.pip)
        )
        self.assertIn(
            self.public_external_version, Version.external.for_project(self.pip)
        )


class TestBuildManagerBase(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        print(self.pip.versions.all())
        # Create a External Version and build. ie: pull/merge request Version.
        self.external_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC
        )
        self.external_version_build = get(
            Build,
            project=self.pip,
            version=self.external_version
        )
        # Create a Internal Version build.
        self.internal_version_build = get(
            Build,
            project=self.pip,
            version=self.pip.versions.get(slug='0.8')
        )

        self.internal_builds = Build.objects.exclude(version__type=EXTERNAL)


class TestInternalBuildManager(TestBuildManagerBase):

    """
    Queries using Internal Manager should only include Internal Version builds.

    It will exclude pull/merge request Version builds from the queries
    and only include BRANCH, TAG, UNKONWN type Versions.
    """

    def test_internal_build_manager_with_all(self):
        self.assertNotIn(self.external_version_build, Build.internal.all())

    def test_internal_build_manager_with_public(self):
        self.assertNotIn(self.external_version_build, Build.internal.public())

    def test_internal_build_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.external_version_build,
            Build.internal.public(self.user, self.pip)
        )

    def test_internal_build_manager_with_api(self):
        self.assertNotIn(self.external_version_build, Build.internal.api())


class TestExternalBuildManager(TestBuildManagerBase):

    """
    Queries using External Manager should only include External Version builds.

    It will only include pull/merge request Version builds in the queries.
    """

    def test_external_build_manager_with_all(self):
        self.assertNotIn(self.internal_builds, Build.external.all())
        self.assertIn(self.external_version_build, Build.external.all())

    def test_external_build_manager_with_public(self):
        self.assertNotIn(self.internal_builds, Build.external.public())
        self.assertIn(self.external_version_build, Build.external.public())

    def test_external_build_manager_with_public_with_user_and_project(self):
        self.assertNotIn(
            self.internal_builds,
            Build.external.public(self.user, self.pip)
        )
        self.assertIn(
            self.external_version_build,
            Build.external.public(self.user, self.pip)
        )

    def test_external_build_manager_with_api(self):
        self.assertNotIn(self.internal_builds, Build.external.api())
        self.assertIn(self.external_version_build, Build.external.api())
