from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import HTMLFile, Project


User = get_user_model()


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
