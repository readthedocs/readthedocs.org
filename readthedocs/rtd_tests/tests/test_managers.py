from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH, EXTERNAL, LATEST, TAG
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import PRIVATE, PROTECTED, PUBLIC
from readthedocs.projects.models import HTMLFile, Project


User = get_user_model()


class TestVersionManagerBase(TestCase):

    def setUp(self):
        self.user = get(User)
        self.another_user = get(User)

        self.pip = get(
            Project,
            slug='pip',
            users=[self.user],
            main_language_project=None,
        )
        self.version_latest = self.pip.versions.get(slug=LATEST)
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
        self.public_version = get(
            Version,
            project=self.pip,
            active=True,
            type=TAG,
            privacy_level=PUBLIC,
        )
        self.private_version = get(
            Version,
            project=self.pip,
            active=True,
            type=TAG,
            privacy_level=PRIVATE,
        )
        self.protected_version = get(
            Version,
            project=self.pip,
            active=True,
            type=TAG,
            privacy_level=PROTECTED,
        )

        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.another_user],
            main_language_project=None,
            versions=[],
        )
        self.another_version_latest = self.another_project.versions.get(slug=LATEST)
        self.another_public_external_version = get(
            Version,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC
        )
        self.another_private_external_version = get(
            Version,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE
        )
        self.another_protected_external_version = get(
            Version,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PROTECTED
        )
        self.another_version_public = get(
            Version,
            privacy_level=PUBLIC,
            project=self.another_project,
            active=True,
        )
        self.another_version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.another_project,
            active=True,
        )
        self.another_version_protected = get(
            Version,
            privacy_level=PROTECTED,
            project=self.another_project,
            active=True,
        )

        self.client.force_login(self.user)


class TestInternalVersionManager(TestVersionManagerBase):

    """
    Queries using Internal Manager should only include Internal Versions.

    It will exclude EXTERNAL type Versions from the queries
    and only include BRANCH, TAG, UNKNOWN type Versions.
    """

    def test_internal_version_manager_with_all(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.protected_version,
            self.private_version,
            self.another_version_latest,
            self.another_version_public,
            self.another_version_protected,
            self.another_version_private,
        }
        query = Version.internal.all()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_public(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.another_version_latest,
            self.another_version_public,
        }
        query = Version.internal.public()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_public_with_user(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.protected_version,
            self.private_version,
            self.another_version_latest,
            self.another_version_public,
        }
        query = Version.internal.public(user=self.user)
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_public_with_user_and_project(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.protected_version,
            self.private_version,
        }
        query = Version.internal.public(self.user, self.pip)
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_protected(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.protected_version,
            self.another_version_latest,
            self.another_version_public,
            self.another_version_protected,
        }
        query = Version.internal.protected()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_private(self):
        versions = {
            self.private_version,
            self.another_version_private,
        }
        query = Version.internal.private()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_api(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.another_version_latest,
            self.another_version_public,
        }
        query = Version.internal.api()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_internal_version_manager_with_for_project(self):
        versions = {
            self.version_latest,
            self.public_version,
            self.protected_version,
            self.private_version,
        }
        query = Version.internal.for_project(self.pip)
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)


class TestExternalVersionManager(TestVersionManagerBase):

    """
    Queries using External Manager should only include External Versions.

    It will only include pull/merge request Version in the queries.
    """

    def test_external_version_manager_with_all(self):
        versions = {
            self.public_external_version,
            self.protected_external_version,
            self.private_external_version,
            self.another_public_external_version,
            self.another_protected_external_version,
            self.another_private_external_version,
        }
        query = Version.external.all()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_public(self):
        versions = {
            self.public_external_version,
            self.another_public_external_version,
        }
        query = Version.external.public()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_public_with_user_and_project(self):
        versions = {
            self.public_external_version,
            self.protected_external_version,
            self.private_external_version,
        }
        query = Version.external.public(self.user, self.pip)
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_protected(self):
        versions = {
            self.public_external_version,
            self.protected_external_version,
            self.another_public_external_version,
            self.another_protected_external_version,
        }
        query = Version.external.protected()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_private(self):
        versions = {
            self.private_external_version,
            self.another_private_external_version,
        }
        query = Version.external.private()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_api(self):
        versions = {
            self.public_external_version,
            self.another_public_external_version,
        }
        query = Version.external.api()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_external_version_manager_with_for_project(self):
        versions = {
            self.public_external_version,
            self.protected_external_version,
            self.private_external_version,
        }
        query = Version.external.for_project(self.pip)
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)


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
    and only include BRANCH, TAG, UNKNOWN type Versions.
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


class TestHTMLFileManager(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.create(username='test_user', password='test')
        self.client.login(username='test_user', password='test')
        self.pip = Project.objects.get(slug='pip')
        # Create a External Version. ie: pull/merge request Version.
        self.external_version = get(
            Version,
            project=self.pip,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC
        )
        self.html_file = HTMLFile.objects.create(
            project=self.pip,
            version=self.external_version,
            name='file.html',
            slug='file',
            path='file.html',
            md5='abcdef',
            commit='1234567890abcdef',
        )
        self.internal_html_files = HTMLFile.objects.exclude(version__type=EXTERNAL)

    def test_internal_html_file_queryset(self):
        """
        It will exclude pull/merge request Version html files from the queries
        and only include BRANCH, TAG, UNKNOWN type Version files.
        """
        self.assertNotIn(self.html_file, HTMLFile.objects.internal())

    def test_external_html_file_queryset(self):
        """
        It will only include pull/merge request Version html files in the queries.
        """
        self.assertNotIn(self.internal_html_files, HTMLFile.objects.external())
        self.assertIn(self.html_file, HTMLFile.objects.external())
