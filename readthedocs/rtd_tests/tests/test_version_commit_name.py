from django.test import TestCase
from django_dynamic_fixture import get, new

from readthedocs.builds.constants import BRANCH, EXTERNAL, LATEST, STABLE, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.constants import REPO_TYPE_GIT
from readthedocs.projects.models import Project


class VersionCommitNameTests(TestCase):
    def test_branch_name_unicode_non_ascii(self):
        unicode_name = b"abc_\xd1\x84_\xe2\x99\x98".decode("utf-8")
        version = new(Version, identifier=unicode_name, type=BRANCH)
        self.assertEqual(version.identifier_friendly, unicode_name)

    def test_branch_name_made_friendly_when_sha(self):
        commit_hash = "3d92b728b7d7b842259ac2020c2fa389f13aff0d"
        version = new(
            Version,
            identifier=commit_hash,
            slug=STABLE,
            verbose_name=STABLE,
            type=TAG,
        )
        # we shorten commit hashes to keep things readable
        self.assertEqual(version.identifier_friendly, "3d92b728")

    def test_branch_name(self):
        version = new(
            Version,
            identifier="release-2.5.x",
            slug="release-2.5.x",
            verbose_name="release-2.5.x",
            type=BRANCH,
        )
        self.assertEqual(version.git_identifier, "release-2.5.x")

    def test_tag_name(self):
        version = new(
            Version,
            identifier="10f1b29a2bd2",
            slug="release-2.5.0",
            verbose_name="release-2.5.0",
            type=TAG,
        )
        self.assertEqual(version.git_identifier, "release-2.5.0")

    def test_branch_with_name_stable(self):
        version = new(
            Version,
            identifier="origin/stable",
            slug=STABLE,
            verbose_name="stable",
            type=BRANCH,
        )
        self.assertEqual(version.git_identifier, "stable")

    def test_stable_version_tag(self):
        version = new(
            Version,
            identifier="3d92b728b7d7b842259ac2020c2fa389f13aff0d",
            slug=STABLE,
            verbose_name=STABLE,
            type=TAG,
            machine=True,
        )
        self.assertEqual(
            version.git_identifier,
            "3d92b728b7d7b842259ac2020c2fa389f13aff0d",
        )

    def test_stable_version_tag_uses_original_stable(self):
        project = get(Project)
        stable = get(
            Version,
            project=project,
            identifier="3d92b728b7d7b842259ac2020c2fa389f13aff0d",
            slug=STABLE,
            verbose_name=STABLE,
            type=TAG,
            machine=True,
        )
        original_stable = get(
            Version,
            project=project,
            identifier="3d92b728b7d7b842259ac2020c2fa389f13aff0d",
            slug="v2.0",
            verbose_name="v2.0",
            type=TAG,
            machine=True,
        )
        self.assertEqual(stable.git_identifier, "v2.0")
        self.assertEqual(original_stable.git_identifier, "v2.0")

    def test_manual_stable_version(self):
        project = get(Project)
        version = get(
            Version,
            project=project,
            identifier="stable",
            slug=STABLE,
            verbose_name=STABLE,
            type=BRANCH,
            machine=False,
        )
        self.assertEqual(version.git_identifier, "stable")

    def test_git_latest_branch(self):
        git_project = get(Project, repo_type=REPO_TYPE_GIT)
        version = new(
            Version,
            project=git_project,
            identifier="master",
            slug=LATEST,
            verbose_name=LATEST,
            type=BRANCH,
            machine=True,
        )
        self.assertEqual(version.git_identifier, "master")

    def test_manual_latest_version(self):
        project = get(Project)
        version = project.versions.get(slug=LATEST)
        version.machine = False
        version.save()
        self.assertEqual(version.git_identifier, "latest")

    def test_external_version(self):
        identifier = "ec26de721c3235aad62de7213c562f8c821"
        version = new(
            Version,
            identifier=identifier,
            slug="11",
            verbose_name="11",
            type=EXTERNAL,
        )
        self.assertEqual(version.git_identifier, "11")
