import os
import textwrap
from os.path import exists
from tempfile import mkdtemp
from unittest import mock
from unittest.mock import Mock, patch

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.builds.constants import BRANCH, EXTERNAL, TAG
from readthedocs.builds.models import Version
from readthedocs.config import ALL
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Feature, Project
from readthedocs.rtd_tests.utils import (
    create_git_branch,
    create_git_tag,
    delete_git_branch,
    delete_git_tag,
    get_current_commit,
    get_git_latest_commit_hash,
    make_test_git,
    make_test_hg,
)


# Avoid trying to save the commands via the API
@mock.patch('readthedocs.doc_builder.environments.BuildCommand.save', mock.MagicMock())
class TestGitBackend(TestCase):
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
        self.build_environment = LocalBuildEnvironment(api_client=mock.MagicMock())

    def tearDown(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.make_clean_working_dir()
        super().tearDown()

    def test_git_lsremote(self):
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
            "with\xa0space",
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        create_git_tag(repo_path, 'v01')
        create_git_tag(repo_path, 'v02', annotated=True)
        create_git_tag(repo_path, 'release-ünîø∂é')

        repo = self.project.vcs_repo(environment=self.build_environment)
        # create the working dir if it not exists. It's required to ``cwd`` to
        # execute the command
        repo.check_working_dir()
        commit = get_current_commit(repo_path)
        repo_branches, repo_tags = repo.lsremote()

        self.assertEqual(
            {branch: branch for branch in default_branches + branches},
            {branch.verbose_name: branch.identifier for branch in repo_branches},
        )

        self.assertEqual(
            {"v01": commit, "v02": commit, "release-ünîø∂é": commit},
            {tag.verbose_name: tag.identifier for tag in repo_tags},
        )

    def test_git_lsremote_tags_only(self):
        repo_path = self.project.repo
        create_git_tag(repo_path, "v01")
        create_git_tag(repo_path, "v02", annotated=True)
        create_git_tag(repo_path, "release-ünîø∂é")

        repo = self.project.vcs_repo(environment=self.build_environment)
        # create the working dir if it not exists. It's required to ``cwd`` to
        # execute the command
        repo.check_working_dir()
        commit = get_current_commit(repo_path)
        repo_branches, repo_tags = repo.lsremote(
            include_tags=True, include_branches=False
        )

        self.assertEqual(repo_branches, [])
        self.assertEqual(
            {"v01": commit, "v02": commit, "release-ünîø∂é": commit},
            {tag.verbose_name: tag.identifier for tag in repo_tags},
        )

    def test_git_lsremote_branches_only(self):
        repo_path = self.project.repo
        default_branches = [
            # comes from ``make_test_git`` function
            "submodule",
            "invalidsubmodule",
        ]
        branches = [
            "develop",
            "master",
            "2.0.X",
            "release/2.0.0",
            "release/foo/bar",
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        repo = self.project.vcs_repo(environment=self.build_environment)
        # create the working dir if it not exists. It's required to ``cwd`` to
        # execute the command
        repo.check_working_dir()
        repo_branches, repo_tags = repo.lsremote(
            include_tags=False, include_branches=True
        )

        self.assertEqual(repo_tags, [])
        self.assertEqual(
            {branch: branch for branch in default_branches + branches},
            {branch.verbose_name: branch.identifier for branch in repo_branches},
        )

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

        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.clone()

        self.assertEqual(
            {branch: branch for branch in default_branches + branches},
            {branch.verbose_name: branch.identifier for branch in repo.branches},
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

        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.clone()

        self.assertEqual(
            set(branches + default_branches),
            {branch.verbose_name for branch in repo.branches},
        )

    def test_git_update_and_checkout(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        code, _, _ = repo.update()
        self.assertEqual(code, 0)

        # Returns `None` because there is no `identifier`,
        # so it uses the default branch
        self.assertIsNone(repo.checkout())

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
            version_type=version.type,
            environment=self.build_environment,
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
            version_type=version.type,
            environment=self.build_environment,
        )
        repo.update()
        code, _, _ = repo.fetch()
        self.assertEqual(code, 0)

    def test_git_checkout_invalid_revision(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
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
        repo = self.project.vcs_repo(environment=self.build_environment)
        # We aren't cloning the repo,
        # so we need to hack the repo path
        repo.working_dir = repo_path
        commit = get_current_commit(repo_path)
        self.assertEqual(
            {"v01": commit, "v02": commit, "release-ünîø∂é": commit},
            {tag.verbose_name: tag.identifier for tag in repo.tags},
        )

    def test_check_for_submodules(self):
        repo = self.project.vcs_repo(environment=self.build_environment)

        repo.update()
        self.assertFalse(repo.are_submodules_available(self.dummy_conf))

        # The submodule branch contains one submodule
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_skip_submodule_checkout(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.update()
        repo.checkout('submodule')
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_use_shallow_clone(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
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
        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.update()
        repo.checkout('submodule')
        valid, _ = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)

    def test_check_invalid_submodule_urls(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
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
        repo = self.project.vcs_repo(environment=self.build_environment)
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

        repo = self.project.vcs_repo(environment=self.build_environment)
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


@mock.patch("readthedocs.doc_builder.environments.BuildCommand.save", mock.MagicMock())
class TestGitBackendNew(TestGitBackend):
    """
    Test the entire Git backend (with the GIT_CLONE_FETCH_CHECKOUT_PATTERN feature flag).

    This test class is intended to maintain all backwards compatibility when introducing new
    git clone+fetch commands, hence inheriting from the former test class.

    Methods have been copied and adapted.
    Once the feature ``GIT_CLONE_FETCH_CHECKOUT_PATTERN`` has become the default for all projects,
    we can discard of TestGitBackend by moving the methods that aren't overwritten into this class
    and renaming it.
    """

    def setUp(self):
        super().setUp()
        fixture.get(
            Feature,
            projects=[self.project],
            feature_id=Feature.GIT_CLONE_FETCH_CHECKOUT_PATTERN,
        )
        self.assertTrue(
            self.project.has_feature(Feature.GIT_CLONE_FETCH_CHECKOUT_PATTERN)
        )

    def test_check_for_submodules(self):
        """
        Test that we can get a branch called 'submodule' containing a valid submodule.
        """
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="submodule",
        )

        repo.update()
        self.assertFalse(repo.are_submodules_available(self.dummy_conf))

        # The submodule branch contains one submodule
        repo.checkout("submodule")
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_check_invalid_submodule_urls(self):
        """Test that a branch with an invalid submodule fails correctly."""
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="invalidsubmodule",
        )
        repo.update()
        repo.checkout("invalidsubmodule")
        with self.assertRaises(RepositoryError) as e:
            repo.update_submodules(self.dummy_conf)
        # `invalid` is created in `make_test_git`
        # it's a url in ssh form.
        self.assertEqual(
            str(e.exception),
            RepositoryError.INVALID_SUBMODULES.format(["invalid"]),
        )

    def test_check_submodule_urls(self):
        """Test that a valid submodule is found in the 'submodule' branch."""
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="submodule",
        )
        repo.update()
        repo.checkout("submodule")
        valid, _ = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)

    @patch("readthedocs.vcs_support.backends.git.Backend.fetch_ng")
    def test_git_update_with_external_version(self, fetch):
        """Test that an external Version (PR) is correctly cloned and fetched."""
        version = fixture.get(
            Version,
            project=self.project,
            type=EXTERNAL,
            active=True,
            identifier="84492ad53ff8aba83015123f4e68d5897a1fd5bc",  # commit hash
            verbose_name="1234",  # pr number
        )
        repo = self.project.vcs_repo(
            verbose_name=version.verbose_name,
            version_type=version.type,
            version_identifier=version.identifier,
            environment=self.build_environment,
        )
        repo.update()
        fetch.assert_called_once()

    def test_invalid_submodule_is_ignored(self):
        """Test that an invalid submodule isn't listed."""
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="submodule",
        )
        repo.update()
        repo.checkout("submodule")
        gitmodules_path = os.path.join(repo.working_dir, ".gitmodules")

        with open(gitmodules_path, "a") as f:
            content = textwrap.dedent(
                """
                [submodule "not-valid-path"]
                    path = not-valid-path
                    url = https://github.com/readthedocs/readthedocs.org
            """
            )
            f.write(content)

        valid, submodules = repo.validate_submodules(self.dummy_conf)
        self.assertTrue(valid)
        self.assertEqual(list(submodules), ["foobar"])

    def test_skip_submodule_checkout(self):
        """Test that a submodule is listed as available."""
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="submodule",
        )
        repo.update()
        repo.checkout("submodule")
        self.assertTrue(repo.are_submodules_available(self.dummy_conf))

    def test_use_shallow_clone(self):
        """A test that should be removed because shallow clones are the new default."""
        # We should not be calling test_use_shallow_clone
        return True

    def test_git_fetch_with_external_version(self):
        """Test that fetching an external build (PR branch) correctly executes."""
        version = fixture.get(Version, project=self.project, type=EXTERNAL, active=True)
        repo = self.project.vcs_repo(
            verbose_name=version.verbose_name,
            version_type=version.type,
            environment=self.build_environment,
        )
        repo.update()
        code, _, _ = repo.fetch_ng()
        self.assertEqual(code, 0)

    def test_git_branches(self):
        """
        Test a source repository with multiple branches, can be cloned and fetched.

        For each branch, we clone and fetch and check that we get exactly what we expect.
        """
        repo_path = self.project.repo
        branches = [
            "develop",
            "master",
            "2.0.X",
            "release/2.0.0",
            "release/foo/bar",
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        for branch in branches:
            # Create a repo that we want to clone and fetch a specific branch for
            repo = self.project.vcs_repo(
                environment=self.build_environment,
                version_identifier=branch,
                version_type=BRANCH,
            )
            # Because current behavior is to reuse already cloned destinations, we should
            # clear the working dir instead of reusing it.
            repo.make_clean_working_dir()

            repo.update()

            self.assertEqual(
                set([branch, "master"]),
                {branch.verbose_name for branch in repo.branches},
            )

    def test_git_branches_unicode(self):
        """Test to verify that we can clone+fetch a unicode branch name."""

        # Add a branch to the repo.
        # Note: It's assumed that the source repo is re-created in setUp()
        create_git_branch(self.project.repo, "release-ünîø∂é")

        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_identifier="release-ünîø∂é",
            version_type=BRANCH,
        )
        repo.update()

        # Note here that the original default branch 'master' got created during the clone
        self.assertEqual(
            set(["release-ünîø∂é", "master"]),
            {branch.verbose_name for branch in repo.branches},
        )

    def test_update_without_branch_name(self):
        """
        Test that we get expected default branch when not specifying a branch name.

        Covers:
        * Manually imported projects +
        * Automatically imported projects that had their default branch name deliberately removed
          during import wizard (and before the first branch sync from webhook)
        """
        repo_path = self.project.repo
        create_git_branch(repo_path, "develop")

        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
        )
        repo.update()

        # Check that the README file from the fixture exists
        self.assertTrue(os.path.isfile(os.path.join(repo.working_dir, "README")))

        # Check that "only-on-default-branch" exists (it doesn't exist on other branches)
        self.assertTrue(
            os.path.exists(os.path.join(repo.working_dir, "only-on-default-branch"))
        )

        # Check that we don't for instance have foobar
        self.assertFalse(os.path.isfile(os.path.join(repo.working_dir, "foobar")))

    def test_special_tag_stable(self):
        """Test that an auto-generated 'stable' tag works."""
        repo_path = self.project.repo
        latest_actual_commit_hash = get_git_latest_commit_hash(repo_path, "master")

        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=TAG,
            version_machine=True,
            version_identifier=latest_actual_commit_hash,
        )
        repo.update()

        # Checkout the master branch to verify that we can checkout something
        # from the above clone+fetch
        repo.checkout("master")


# Avoid trying to save the commands via the API
@mock.patch('readthedocs.doc_builder.environments.BuildCommand.save', mock.MagicMock())
class TestHgBackend(TestCase):

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
        self.build_environment = LocalBuildEnvironment(api_client=mock.MagicMock())

    def test_parse_branches(self):
        data = """\
        stable
        default
        """

        expected_ids = ["stable", "default"]
        given_ids = [
            x.identifier
            for x in self.project.vcs_repo(
                environment=self.build_environment
            ).parse_branches(data)
        ]
        self.assertEqual(expected_ids, given_ids)

    def test_update_and_checkout(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.make_clean_working_dir()
        code, _, _ = repo.update()
        self.assertEqual(code, 0)
        code, _, _ = repo.checkout()
        self.assertEqual(code, 0)
        self.assertTrue(exists(repo.working_dir))

    def test_checkout_invalid_revision(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
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

        given_ids = [
            (x.identifier, x.verbose_name)
            for x in self.project.vcs_repo(
                environment=self.build_environment
            ).parse_tags(data)
        ]
        self.assertEqual(expected_tags, given_ids)
