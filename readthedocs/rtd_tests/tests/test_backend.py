# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from os.path import exists

import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from mock import Mock

from readthedocs.config import ALL
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Feature, Project
from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.rtd_tests.utils import (
    create_git_tag, make_test_git, make_test_hg)


class TestGitBackend(RTDTestCase):
    def setUp(self):
        git_repo = make_test_git()
        super(TestGitBackend, self).setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="git",
            #Our top-level checkout
            repo=git_repo
        )
        self.project.users.add(self.eric)
        self.dummy_conf = Mock()
        # These are the default values from v1
        self.dummy_conf.submodules.include = ALL
        self.dummy_conf.submodules.exclude = []

    def test_parse_branches(self):
        data = """
        develop
        master
        release/2.0.0
        origin/2.0.X
        origin/HEAD -> origin/master
        origin/master
        origin/release/2.0.0
        origin/release/foo/bar
        """

        expected_ids = [
            ('develop', 'develop'),
            ('master', 'master'),
            ('release/2.0.0', 'release/2.0.0'),
            ('origin/2.0.X', '2.0.X'),
            ('origin/master', 'master'),
            ('origin/release/2.0.0', 'release/2.0.0'),
            ('origin/release/foo/bar', 'release/foo/bar'),
        ]
        given_ids = [(x.identifier, x.verbose_name) for x in
                     self.project.vcs_repo().parse_branches(data)]
        self.assertEqual(expected_ids, given_ids)

    def test_git_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout()
        self.assertTrue(exists(repo.working_dir))

    def test_git_tags(self):
        repo_path = self.project.repo
        create_git_tag(repo_path, 'v01')
        create_git_tag(repo_path, 'v02', annotated=True)
        create_git_tag(repo_path, 'release-ünîø∂é')
        repo = self.project.vcs_repo()
        # We aren't cloning the repo,
        # so we need to hack the repo path
        repo.working_dir = repo_path
        self.assertEqual(
            set(['v01', 'v02', 'release-ünîø∂é']),
            set(vcs.verbose_name for vcs in repo.tags)
        )

    def test_check_for_submodules(self):
        repo = self.project.vcs_repo()

        repo.checkout()
        self.assertFalse(repo.are_submodules_available(self.dummy_conf))

        # The submodule branch contains one submodule
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_skip_submodule_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))
        feature = fixture.get(
            Feature,
            projects=[self.project],
            feature_id=Feature.SKIP_SUBMODULES,
        )
        self.assertTrue(self.project.has_feature(Feature.SKIP_SUBMODULES))
        self.assertFalse(repo.are_submodules_available(self.dummy_conf))

    def test_check_submodule_urls(self):
        repo = self.project.vcs_repo()
        repo.checkout('submodule')
        valid, _ = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)
        repo.checkout('relativesubmodule')
        valid, _ = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)

    @pytest.mark.xfail(strict=True, reason="Fixture is not working correctly")
    def test_check_invalid_submodule_urls(self):
        with self.assertRaises(RepositoryError) as e:
            repo.checkout('invalidsubmodule')
            self.assertEqual(e.msg, RepositoryError.INVALID_SUBMODULES)


class TestHgBackend(RTDTestCase):
    def setUp(self):
        hg_repo = make_test_hg()
        super(TestHgBackend, self).setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="hg",
            #Our top-level checkout
            repo=hg_repo
        )
        self.project.users.add(self.eric)

    def test_parse_branches(self):
        data = """\
        stable
        default
        """

        expected_ids = ['stable', 'default']
        given_ids = [x.identifier for x in
                     self.project.vcs_repo().parse_branches(data)]
        self.assertEqual(expected_ids, given_ids)

    def test_checkout(self):
        repo = self.project.vcs_repo()
        repo.checkout()
        self.assertTrue(exists(repo.working_dir))

    def test_parse_tags(self):
        data = """\
        tip                            13575:8e94a1b4e9a4
        1.8.1                          13573:aa1f3be38ab1
        1.8                            13515:2616325766e3
        1.7.5                          13334:2b2155623ee2
         """
        expected_tags = [
            ('aa1f3be38ab1', '1.8.1'),
            ('2616325766e3', '1.8'),
            ('2b2155623ee2', '1.7.5'),
        ]

        given_ids = [(x.identifier, x.verbose_name) for x in
                     self.project.vcs_repo().parse_tags(data)]
        self.assertEqual(expected_tags, given_ids)
