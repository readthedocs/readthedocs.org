# -*- coding: utf-8 -*-

import os
from os.path import exists
from tempfile import mkdtemp
import textwrap

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from mock import Mock, patch

from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.models import Version
from readthedocs.config import ALL
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Feature, Project
from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.rtd_tests.utils import (
    create_git_branch,
    create_git_tag,
    delete_git_branch,
    delete_git_tag,
    make_test_git,
    make_test_hg,
)


class TestGitBackend(RTDTestCase):
    def setUp(self):
        git_repo = make_test_git()
        super().setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name='Test Project',
            repo_type='git',
            #Our top-level checkout
            repo=git_repo,
        )
        self.project.users.add(self.eric)
        self.dummy_conf = Mock()
        # These are the default values from v1
        self.dummy_conf.submodules.include = ALL
        self.dummy_conf.submodules.exclude = []

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_git_branches(self, checkout_path):
        repo_path = self.project.repo
        default_branches = [
            # comes from ``make_test_git`` function
            'submodule',
            'invalidsubmodule',
        ]
        branches = [
            'develop',
            'master',
            '2.0.X',
            'release/2.0.0',
            'release/foo/bar',
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        repo = self.project.vcs_repo()
        repo.clone()

        self.assertEqual(
            set(branches + default_branches),
            {branch.verbose_name for branch in repo.branches},
        )

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_git_branches_unicode(self, checkout_path):
        repo_path = self.project.repo
        default_branches = [
            # comes from ``make_test_git`` function
            'submodule',
            'invalidsubmodule',
        ]
        branches = [
            'master',
            'release-ünîø∂é',
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        repo = self.project.vcs_repo()
        repo.clone()

        self.assertEqual(
            set(branches + default_branches),
            {branch.verbose_name for branch in repo.branches},
        )

    def test_git_update_and_checkout(self):
        repo = self.project.vcs_repo()
        code, _, _ = repo.update()
        self.assertEqual(code, 0)
        code, _, _ = repo.checkout()
        self.assertEqual(code, 0)
        self.assertTrue(exists(repo.working_dir))

    @patch('readthedocs.vcs_support.backends.git.Backend.fetch')
    def test_git_update_with_external_version(self, fetch):
        version = fixture.get(
            Version,
            project=self.project,
            type=EXTERNAL,
            active=True
        )
        repo = self.project.vcs_repo(
            verbose_name=version.verbose_name,
            version_type=version.type
        )
        repo.update()
        fetch.assert_called_once()

    def test_git_fetch_with_external_version(self):
        version = fixture.get(
            Version,
            project=self.project,
            type=EXTERNAL,
            active=True
        )
        repo = self.project.vcs_repo(
            verbose_name=version.verbose_name,
            version_type=version.type
        )
        repo.update()
        code, _, _ = repo.fetch()
        self.assertEqual(code, 0)

    def test_git_checkout_invalid_revision(self):
        repo = self.project.vcs_repo()
        repo.update()
        version = 'invalid-revision'
        with self.assertRaises(RepositoryError) as e:
            repo.checkout(version)
        self.assertEqual(
            str(e.exception),
            RepositoryError.FAILED_TO_CHECKOUT.format(version),
        )

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
            {'v01', 'v02', 'release-ünîø∂é'},
            {vcs.verbose_name for vcs in repo.tags},
        )

    def test_check_for_submodules(self):
        repo = self.project.vcs_repo()

        repo.update()
        self.assertFalse(repo.are_submodules_available(self.dummy_conf))

        # The submodule branch contains one submodule
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_skip_submodule_checkout(self):
        repo = self.project.vcs_repo()
        repo.update()
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_use_shallow_clone(self):
        repo = self.project.vcs_repo()
        repo.update()
        repo.checkout('submodule')
        self.assertTrue(repo.use_shallow_clone())
        fixture.get(
            Feature,
            projects=[self.project],
            feature_id=Feature.DONT_SHALLOW_CLONE,
        )
        self.assertTrue(self.project.has_feature(Feature.DONT_SHALLOW_CLONE))
        self.assertFalse(repo.use_shallow_clone())

    def test_check_submodule_urls(self):
        repo = self.project.vcs_repo()
        repo.update()
        repo.checkout('submodule')
        valid, _ = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)

    def test_check_invalid_submodule_urls(self):
        repo = self.project.vcs_repo()
        repo.update()
        repo.checkout('invalidsubmodule')
        with self.assertRaises(RepositoryError) as e:
            repo.update_submodules(self.dummy_conf)
        # `invalid` is created in `make_test_git`
        # it's a url in ssh form.
        self.assertEqual(
            str(e.exception),
            RepositoryError.INVALID_SUBMODULES.format(['invalid']),
        )

    def test_invalid_submodule_is_ignored(self):
        repo = self.project.vcs_repo()
        repo.update()
        repo.checkout('submodule')
        gitmodules_path = os.path.join(repo.working_dir, '.gitmodules')

        with open(gitmodules_path, 'a') as f:
            content = textwrap.dedent("""
                [submodule "not-valid-path"]
                    path = not-valid-path
                    url = https://github.com/readthedocs/readthedocs.org
            """)
            f.write(content)

        valid, submodules = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)
        self.assertEqual(list(submodules), ['foobar'])

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_fetch_clean_tags_and_branches(self, checkout_path):
        upstream_repo = self.project.repo
        create_git_tag(upstream_repo, 'v01')
        create_git_tag(upstream_repo, 'v02')
        create_git_branch(upstream_repo, 'newbranch')

        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        repo = self.project.vcs_repo()
        repo.clone()

        delete_git_tag(upstream_repo, 'v02')
        delete_git_branch(upstream_repo, 'newbranch')

        # We still have all branches and tags in the local repo
        self.assertEqual(
            {'v01', 'v02'},
            {vcs.verbose_name for vcs in repo.tags},
        )
        self.assertEqual(
            {
                'invalidsubmodule', 'master', 'submodule', 'newbranch',
            },
            {vcs.verbose_name for vcs in repo.branches},
        )

        repo.update()

        # We don't have the eliminated branches and tags in the local repo
        self.assertEqual(
            {'v01'},
            {vcs.verbose_name for vcs in repo.tags},
        )
        self.assertEqual(
            {
                'invalidsubmodule', 'master', 'submodule',
            },
            {vcs.verbose_name for vcs in repo.branches},
        )


class TestHgBackend(RTDTestCase):

    def setUp(self):
        hg_repo = make_test_hg()
        super().setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name='Test Project',
            repo_type='hg',
            # Our top-level checkout
            repo=hg_repo,
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

    def test_update_and_checkout(self):
        repo = self.project.vcs_repo()
        code, _, _ = repo.update()
        self.assertEqual(code, 0)
        code, _, _ = repo.checkout()
        self.assertEqual(code, 0)
        self.assertTrue(exists(repo.working_dir))

    def test_checkout_invalid_revision(self):
        repo = self.project.vcs_repo()
        repo.update()
        version = 'invalid-revision'
        with self.assertRaises(RepositoryError) as e:
            repo.checkout(version)
        self.assertEqual(
            str(e.exception),
            RepositoryError.FAILED_TO_CHECKOUT.format(version),
        )

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
