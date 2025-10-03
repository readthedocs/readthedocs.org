from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import EXTERNAL, INTERNAL, LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import Project


class TestVersionQuerySetBase(TestCase):
    def setUp(self):
        self.user = get(User)
        self.another_user = get(User)

        self.project = get(
            Project,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
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

        self.another_project = get(
            Project,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
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

        self.shared_project = get(
            Project,
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
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

        self.user_versions = {
            self.version,
            self.version_latest,
            self.version_private,
            self.shared_version,
            self.shared_version_latest,
            self.shared_version_private,
        }

        self.another_user_versions = {
            self.another_version_latest,
            self.another_version,
            self.another_version_private,
            self.shared_version,
            self.shared_version_latest,
            self.shared_version_private,
        }


class VersionQuerySetTests(TestVersionQuerySetBase):
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
        versions = self.user_versions | {
            self.another_version_latest,
            self.another_version,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_project(self):
        query = self.project.versions.public(user=self.user)
        versions = {
            self.version,
            self.version_latest,
            self.version_private,
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


class TestVersionQuerySetWithManagerBase(TestVersionQuerySetBase):
    def setUp(self):
        super().setUp()

        self.external_version_public = get(
            Version,
            project=self.project,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC,
        )
        self.external_version_private = get(
            Version,
            project=self.project,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE,
        )

        self.another_external_version_public = get(
            Version,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC,
        )
        self.another_external_version_private = get(
            Version,
            project=self.another_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE,
        )

        self.shared_external_version_public = get(
            Version,
            project=self.shared_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PUBLIC,
        )
        self.shared_external_version_private = get(
            Version,
            project=self.shared_project,
            active=True,
            type=EXTERNAL,
            privacy_level=PRIVATE,
        )


class VersionQuerySetWithInternalManagerTest(TestVersionQuerySetWithManagerBase):

    """
    Queries using Internal Manager should only include Internal Versions.

    It will exclude EXTERNAL type Versions from the queries
    and only include BRANCH, TAG, UNKNOWN type Versions.
    """

    def test_all(self):
        query = Version.internal.all()
        versions = {
            self.version_latest,
            self.version,
            self.version_private,
            self.another_version_latest,
            self.another_version,
            self.another_version_private,
            self.shared_version_latest,
            self.shared_version,
            self.shared_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public(self):
        query = Version.internal.public()
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
        query = Version.internal.public(user=self.user)
        versions = self.user_versions | {
            self.another_version_latest,
            self.another_version,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_project(self):
        query = self.project.versions(manager=INTERNAL).public(user=self.user)
        versions = {
            self.version,
            self.version_latest,
            self.version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_api(self):
        query = Version.internal.api()
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


class VersionQuerySetWithExternalManagerTest(TestVersionQuerySetWithManagerBase):

    """
    Queries using External Manager should only include External Versions.

    It will only include pull/merge request Version in the queries.
    """

    def test_all(self):
        query = Version.external.all()
        versions = {
            self.external_version_public,
            self.external_version_private,
            self.another_external_version_public,
            self.another_external_version_private,
            self.shared_external_version_public,
            self.shared_external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_with_private_external_versions(self):
        self.project.external_builds_privacy_level = PRIVATE
        self.project.save()
        self.another_project.external_builds_privacy_level = PRIVATE
        self.another_project.save()
        self.shared_project.external_builds_privacy_level = PRIVATE
        self.shared_project.save()
        query = Version.external.public()
        versions = set()
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_with_some_private_external_versions(self):
        self.another_project.external_builds_privacy_level = PRIVATE
        self.another_project.save()
        self.shared_project.external_builds_privacy_level = PRIVATE
        self.shared_project.save()
        query = Version.external.public()
        versions = {
            self.external_version_public,
            self.external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_with_public_external_versions(self):
        query = Version.external.public()
        versions = {
            self.external_version_public,
            self.external_version_private,
            self.shared_external_version_public,
            self.shared_external_version_private,
            self.another_external_version_public,
            self.another_external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_user(self):
        self.project.external_builds_privacy_level = PRIVATE
        self.project.save()
        self.another_project.external_builds_privacy_level = PRIVATE
        self.another_project.save()
        query = Version.external.public(user=self.user)
        versions = {
            self.external_version_public,
            self.external_version_private,
            self.shared_external_version_public,
            self.shared_external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_public_project(self):
        query = self.project.versions(manager=EXTERNAL).public(user=self.user)
        versions = {
            self.external_version_public,
            self.external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)

    def test_api(self):
        self.project.external_builds_privacy_level = PRIVATE
        self.project.save()
        self.another_project.external_builds_privacy_level = PRIVATE
        self.another_project.save()
        query = Version.external.api()
        versions = {
            self.shared_external_version_public,
            self.shared_external_version_private,
        }
        self.assertEqual(query.count(), len(versions))
        self.assertEqual(set(query), versions)
