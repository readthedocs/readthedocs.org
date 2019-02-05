# -*- coding: utf-8 -*-
from django.test import TestCase
from django_dynamic_fixture import get, new

from readthedocs.builds.constants import BRANCH, LATEST, STABLE, TAG
from readthedocs.builds.models import Version
from readthedocs.projects.constants import REPO_TYPE_GIT, REPO_TYPE_HG
from readthedocs.projects.models import Project


class VersionCommitNameTests(TestCase):
    def test_branch_name_unicode_non_ascii(self):
        unicode_name = b'abc_\xd1\x84_\xe2\x99\x98'.decode('utf-8')
        version = new(Version, identifier=unicode_name, type=BRANCH)
        self.assertEqual(version.identifier_friendly, unicode_name)

    def test_branch_name_made_friendly_when_sha(self):
        commit_hash = '3d92b728b7d7b842259ac2020c2fa389f13aff0d'
        version = new(
            Version, identifier=commit_hash,
            slug=STABLE, verbose_name=STABLE, type=TAG,
        )
        # we shorten commit hashes to keep things readable
        self.assertEqual(version.identifier_friendly, '3d92b728')

    def test_branch_name(self):
        version = new(
            Version, identifier='release-2.5.x',
            slug='release-2.5.x', verbose_name='release-2.5.x',
            type=BRANCH,
        )
        self.assertEqual(version.commit_name, 'release-2.5.x')

    def test_tag_name(self):
        version = new(
            Version, identifier='10f1b29a2bd2', slug='release-2.5.0',
            verbose_name='release-2.5.0', type=TAG,
        )
        self.assertEqual(version.commit_name, 'release-2.5.0')

    def test_branch_with_name_stable(self):
        version = new(
            Version, identifier='origin/stable', slug=STABLE,
            verbose_name='stable', type=BRANCH,
        )
        self.assertEqual(version.commit_name, 'stable')

    def test_stable_version_tag(self):
        version = new(
            Version,
            identifier='3d92b728b7d7b842259ac2020c2fa389f13aff0d',
            slug=STABLE, verbose_name=STABLE, type=TAG,
        )
        self.assertEqual(
            version.commit_name,
            '3d92b728b7d7b842259ac2020c2fa389f13aff0d',
        )

    def test_hg_latest_branch(self):
        hg_project = get(Project, repo_type=REPO_TYPE_HG)
        version = new(
            Version, identifier='default', slug=LATEST,
            verbose_name=LATEST, type=BRANCH, project=hg_project,
        )
        self.assertEqual(version.commit_name, 'default')

    def test_git_latest_branch(self):
        git_project = get(Project, repo_type=REPO_TYPE_GIT)
        version = new(
            Version, project=git_project,
            identifier='origin/master', slug=LATEST,
            verbose_name=LATEST, type=BRANCH,
        )
        self.assertEqual(version.commit_name, 'master')
