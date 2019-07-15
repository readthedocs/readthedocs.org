from django_dynamic_fixture import get
from django.contrib.auth.models import User
from django.test import TestCase
from readthedocs.projects.models import Project
from readthedocs.projects.constants import PRIVATE, PUBLIC, PROTECTED
from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version


class VersionQuerySetTests(TestCase):

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
        self.version_latest = self.project.versions.get(slug=LATEST)
        self.version = get(
            Version,
            privacy_level=PUBLIC,
            project=self.project,
            active=True,
        )
        self.version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.project,
            active=True,
        )
        self.version_protected = get(
            Version,
            privacy_level=PROTECTED,
            project=self.project,
            active=True,
        )

        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.another_user],
            main_language_project=None,
            versions=[],
        )
        self.another_version_latest = self.another_project.versions.get(slug=LATEST)
        self.another_version = get(
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

        self.shared_project = get(
            Project,
            privacy_level=PUBLIC,
            users=[self.user, self.another_user],
            main_language_project=None,
            versions=[],
        )
        self.shared_version_latest = self.shared_project.versions.get(slug=LATEST)
        self.shared_version = get(
            Version,
            privacy_level=PUBLIC,
            project=self.shared_project,
            active=True,
        )
        self.shared_version_private = get(
            Version,
            privacy_level=PRIVATE,
            project=self.shared_project,
            active=True,
        )
        self.shared_version_protected = get(
            Version,
            privacy_level=PROTECTED,
            project=self.shared_project,
            active=True,
        )

        self.user_versions = {
            self.version,
            self.version_latest,
            self.version_private,
            self.version_protected,
            self.shared_version,
            self.shared_version_latest,
            self.shared_version_private,
            self.shared_version_protected,
        }

        self.another_user_versions = {
            self.another_version_latest,
            self.another_version,
            self.another_version_private,
            self.another_version_protected,
            self.shared_version,
            self.shared_version_latest,
            self.shared_version_private,
            self.shared_version_protected,
        }

    def test_public(self):
        query = Version.objects.public()
        versions = {
            self.version_latest,
            self.version,
            self.another_version,
            self.another_version_latest,
            self.shared_version,
            self.shared_version_latest,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_user(self):
        query = Version.objects.public(user=self.user)
        versions = (
            self.user_versions |
            {self.another_version_latest, self.another_version}
        )
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_project(self):
        query = Version.objects.public(user=self.user, project=self.project)
        versions = {
            self.version,
            self.version_latest,
            self.version_private,
            self.version_protected,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_protected(self):
        query = Version.objects.protected()
        versions = {
            self.version,
            self.version_latest,
            self.version_protected,
            self.another_version,
            self.another_version_latest,
            self.another_version_protected,
            self.shared_version,
            self.shared_version_latest,
            self.shared_version_protected,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_protected_user(self):
        query = Version.objects.protected(user=self.user)
        versions = (
            self.user_versions |
            {
                self.another_version,
                self.another_version_latest,
                self.another_version_protected,
            }
        )
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_protected_project(self):
        query = Version.objects.protected(user=self.user, project=self.project)
        versions = {
            self.version,
            self.version_latest,
            self.version_private,
            self.version_protected,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_private(self):
        query = Version.objects.private()
        versions = {
            self.version_private,
            self.another_version_private,
            self.shared_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_private_user(self):
        query = Version.objects.private(user=self.user)
        versions = (
            self.user_versions |
            {self.another_version_private}
        )
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_private_project(self):
        query = Version.objects.private(user=self.user, project=self.project)
        versions = {
            self.version,
            self.version_latest,
            self.version_private,
            self.version_protected,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_api(self):
        query = Version.objects.api()
        versions = {
            self.version_latest,
            self.version,
            self.another_version,
            self.another_version_latest,
            self.shared_version,
            self.shared_version_latest,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_api_user(self):
        query = Version.objects.api(user=self.user, detail=False)
        versions = self.user_versions
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_for_project(self):
        self.another_project.main_language_project = self.project
        self.another_project.save()

        query = Version.objects.for_project(self.project)
        versions = {
            self.version,
            self.version_latest,
            self.version_protected,
            self.version_private,
            self.another_version,
            self.another_version_latest,
            self.another_version_protected,
            self.another_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)
