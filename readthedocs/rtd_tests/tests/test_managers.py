from django.contrib.auth import get_user_model
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import HTMLFile, Project


User = get_user_model()


class TestBuildManagerBase(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.user = get(User)
        self.another_user = get(User)

        self.project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.user],
            main_language_project=None,
            versions=[],
        )
        self.version_public = get(
            Version,
            privacy_level=PUBLIC,
            project=self.project,
            active=True,
            slug='version_public'
        )
        self.build_public = get(
            Build,
            version=self.version_public,
            project=self.project,
        )
        self.version_public_external = get(
            Version,
            privacy_level=PUBLIC,
            project=self.project,
            active=True,
            type=EXTERNAL,
            slug='version_public_external'
        )
        self.build_public_external = get(
            Build,
            version=self.version_public_external,
            project=self.project,
        )
        self.version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.project,
            active=True,
            slug='version_private'
        )
        self.build_private = get(
            Build,
            version=self.version_private,
            project=self.project,
        )
        self.version_private_external = get(
            Version,
            privacy_level=PRIVATE,
            project=self.project,
            active=True,
            type=EXTERNAL,
            slug='version_private_external'
        )
        self.build_private_external = get(
            Build,
            version=self.version_private_external,
            project=self.project,
        )

        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.another_user],
            main_language_project=None,
            versions=[],
        )
        self.another_version_public = get(
            Version,
            privacy_level=PUBLIC,
            project=self.another_project,
            active=True,
            slug='another_version_public'
        )
        self.another_build_public = get(
            Build,
            version=self.another_version_public,
            project=self.another_project,
        )
        self.another_version_public_external = get(
            Version,
            privacy_level=PUBLIC,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            slug='another_version_public_external'
        )
        self.another_build_public_external = get(
            Build,
            version=self.another_version_public_external,
            project=self.another_project,
        )
        self.another_version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.another_project,
            active=True,
            slug='another_version_private'
        )
        self.another_build_private = get(
            Build,
            version=self.another_version_private,
            project=self.another_project,
        )
        self.another_version_private_external = get(
            Version,
            privacy_level=PRIVATE,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            slug='another_version_private_external'
        )
        self.another_build_private_external = get(
            Build,
            version=self.another_version_private_external,
            project=self.another_project,
        )

        self.shared_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.user, self.another_user],
            main_language_project=None,
            versions=[],
        )
        self.shared_version_public = get(
            Version,
            privacy_level=PUBLIC,
            project=self.shared_project,
            active=True,
            slug='shared_version_public'
        )
        self.shared_build_public = get(
            Build,
            version=self.shared_version_public,
            project=self.shared_project,
        )
        self.shared_version_public_external = get(
            Version,
            privacy_level=PUBLIC,
            project=self.shared_project,
            active=True,
            type=EXTERNAL,
            slug='shared_version_public_external'
        )
        self.shared_build_public_external = get(
            Build,
            version=self.shared_version_public_external,
            project=self.shared_project,
        )
        self.shared_version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.shared_project,
            active=True,
            slug='shared_version_private'
        )
        self.shared_build_private = get(
            Build,
            version=self.shared_version_private,
            project=self.shared_project,
        )
        self.shared_version_private_external = get(
            Version,
            privacy_level=PRIVATE,
            project=self.shared_project,
            active=True,
            type=EXTERNAL,
            slug='shared_version_private_external'
        )
        self.shared_build_private_external = get(
            Build,
            version=self.shared_version_private_external,
            project=self.shared_project,
        )

        self.all_builds = {
            self.build_private,
            self.build_private_external,
            self.another_build_private,
            self.another_build_private_external,
            self.shared_build_private,
            self.shared_build_private_external,
            self.build_public,
            self.build_public_external,
            self.another_build_public,
            self.another_build_public_external,
            self.shared_build_public,
            self.shared_build_public_external,
        }

        self.external_builds = {
            self.build_private_external,
            self.another_build_private_external,
            self.shared_build_private_external,
            self.build_public_external,
            self.another_build_public_external,
            self.shared_build_public_external,
        }
        self.user_builds = {
            self.build_private,
            self.build_private_external,
            self.shared_build_private,
            self.shared_build_private_external,
            self.build_public,
            self.build_public_external,
            self.shared_build_public,
            self.shared_build_public_external,
        }

        self.another_user_builds = {
            self.another_build_private,
            self.another_build_private_external,
            self.shared_build_private,
            self.shared_build_private_external,
            self.another_build_public,
            self.another_build_public_external,
            self.shared_build_public,
            self.shared_build_public_external,
        }


class TestInternalBuildManager(TestBuildManagerBase):

    """
    Queries using Internal Manager should only include Internal Version builds.

    It will exclude pull/merge request Version builds from the queries
    and only include BRANCH, TAG, UNKNOWN type Versions.
    """

    def test_all(self):
        query = Build.internal.all()
        internal_builds = {
            self.build_private,
            self.another_build_private,
            self.shared_build_private,
            self.build_public,
            self.another_build_public,
            self.shared_build_public,
        }
        self.assertEqual(query.count(), len(internal_builds))
        self.assertEqual(set(query), internal_builds)

    def test_public(self):
        query = Build.internal.public()
        public_internal_builds = {
            self.build_public,
            self.another_build_public,
            self.shared_build_public,
        }
        self.assertEqual(query.count(), len(public_internal_builds))
        self.assertEqual(set(query), public_internal_builds)

    def test_public_user(self):
        query = Build.internal.public(user=self.user)
        builds = {
            self.build_private,
            self.shared_build_private,
            self.build_public,
            self.shared_build_public,
            self.another_build_public,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_public_project(self):
        query = Build.internal.public(user=self.user, project=self.project)
        builds = {
            self.build_private,
            self.build_public,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_api(self):
        query = Build.internal.api(user=self.user)
        builds = {
            self.build_private,
            self.shared_build_private,
            self.build_public,
            self.shared_build_public,
            self.another_build_public,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_api_user(self):
        query = Build.internal.api(user=self.user, detail=False)
        builds = {
            self.build_private,
            self.shared_build_private,
            self.build_public,
            self.shared_build_public,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)


class TestExternalBuildManager(TestBuildManagerBase):

    """
    Queries using External Manager should only include External Version builds.

    It will only include pull/merge request Version builds in the queries.
    """

    def test_all(self):
        query = Build.external.all()
        external_builds = {
            self.build_private_external,
            self.another_build_private_external,
            self.shared_build_private_external,
            self.build_public_external,
            self.another_build_public_external,
            self.shared_build_public_external,
        }
        self.assertEqual(query.count(), len(external_builds))
        self.assertEqual(set(query), external_builds)

    def test_public(self):
        query = Build.external.public()
        public_external_builds = {
            self.build_public_external,
            self.another_build_public_external,
            self.shared_build_public_external,
        }
        self.assertEqual(query.count(), len(public_external_builds))
        self.assertEqual(set(query), public_external_builds)

    def test_public_user(self):
        query = Build.external.public(user=self.user)
        builds = {
            self.build_private_external,
            self.shared_build_private_external,
            self.build_public_external,
            self.another_build_public_external,
            self.shared_build_public_external,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_public_project(self):
        query = Build.external.public(user=self.user, project=self.project)
        builds = {
            self.build_private_external,
            self.build_public_external,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_api(self):
        query = Build.external.api(user=self.user)
        builds = {
            self.build_private_external,
            self.shared_build_private_external,
            self.build_public_external,
            self.another_build_public_external,
            self.shared_build_public_external,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)

    def test_api_user(self):
        query = Build.external.api(user=self.user, detail=False)
        builds = {
            self.build_private_external,
            self.shared_build_private_external,
            self.build_public_external,
            self.shared_build_public_external,
        }
        self.assertEqual(query.count(), len(builds))
        self.assertEqual(set(query), builds)


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
        self.internal_version = get(
            Version,
            project=self.pip,
            active=True,
            privacy_level=PUBLIC
        )
        self.external_html_file = HTMLFile.objects.create(
            project=self.pip,
            version=self.external_version,
            name='file.html',
            slug='file',
            path='file.html',
            md5='abcdef',
            commit='1234567890abcdef',
        )
        self.internal_html_file = HTMLFile.objects.create(
            project=self.pip,
            version=self.internal_version,
            name='file.html',
            slug='file',
            path='file.html',
            md5='abcdef',
            commit='1234567890abcdef',
        )

    def test_internal_html_file_queryset(self):
        """
        It will exclude pull/merge request Version html files from the queries
        and only include BRANCH, TAG, UNKNOWN type Version files.
        """
        self.assertNotIn(self.external_html_file, HTMLFile.objects.internal())
        self.assertIn(self.internal_html_file, HTMLFile.objects.internal())

    def test_external_html_file_queryset(self):
        """
        It will only include pull/merge request Version html files in the queries.
        """
        self.assertNotIn(self.internal_html_file, HTMLFile.objects.external())
        self.assertIn(self.external_html_file, HTMLFile.objects.external())
