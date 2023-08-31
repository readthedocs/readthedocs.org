import os
import textwrap
from os.path import exists
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
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.utils import (
    create_git_branch,
    create_git_tag,
    get_current_commit,
    get_git_latest_commit_hash,
    make_test_git,
    make_test_hg,
)


# Avoid trying to save the commands via the API
@mock.patch("readthedocs.doc_builder.environments.BuildCommand.save", mock.MagicMock())
class TestGitBackend(TestCase):
    def setUp(self):
        git_repo = make_test_git()
        super().setUp()
        self.eric = User(username="eric")
        self.eric.set_password("test")
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="git",
            # Our top-level checkout
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
            "submodule",
            "invalidsubmodule",
        ]
        branches = [
            "develop",
            "master",
            "2.0.X",
            "release/2.0.0",
            "release/foo/bar",
            "with\xa0space",
        ]
        for branch in branches:
            create_git_branch(repo_path, branch)

        create_git_tag(repo_path, "v01")
        create_git_tag(repo_path, "v02", annotated=True)
        create_git_tag(repo_path, "release-ünîø∂é")

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

    def test_git_update_and_checkout(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        code, _, _ = repo.update()
        self.assertEqual(code, 0)

        # Returns `None` because there is no `identifier`,
        # so it uses the default branch
        self.assertIsNone(repo.checkout())

        self.assertTrue(exists(repo.working_dir))

    def test_git_checkout_invalid_revision(self):
        repo = self.project.vcs_repo(environment=self.build_environment)
        repo.update()
        version = "invalid-revision"
        with self.assertRaises(RepositoryError) as e:
            repo.checkout(version)
        self.assertEqual(
            str(e.exception),
            RepositoryError.FAILED_TO_CHECKOUT.format(version),
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

    def test_check_submodule_urls(self):
        """Test that a valid submodule is found in the 'submodule' branch."""
        repo = self.project.vcs_repo(
            environment=self.build_environment,
            version_type=BRANCH,
            version_identifier="submodule",
        )
        repo.update()
        repo.checkout("submodule")
        valid, _ = repo.get_available_submodules(self.dummy_conf)
        self.assertTrue(valid)

    @patch("readthedocs.vcs_support.backends.git.Backend.fetch")
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

    def test_submodule_without_url_is_included(self):
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
                    url =
                """
            )
            f.write(content)

        submodules = list(repo.submodules)
        self.assertEqual(submodules, ["foobar", "not-valid-path"])

    def test_parse_submodules(self):
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
                    url =

                [submodule "path with spaces"]
                    path = path with spaces
                    url = https://github.com

                [submodule "another-submodule"]
                    url = https://github.com
                    path = another-submodule

                [ssubmodule "invalid-submodule-key"]
                    url = https://github.com
                    path = invalid-submodule-key

                [submodule "invalid-path-key"]
                    url = https://github.com
                    paths = invalid-submodule-key

                [submodule "invalid-url-key"]
                    uurl = https://github.com
                    path = invalid-submodule-key
                """
            )
            f.write(content)

        submodules = list(repo.submodules)
        self.assertEqual(
            submodules,
            [
                "foobar",
                "not-valid-path",
                "path with spaces",
                "another-submodule",
                "invalid-submodule-key",
            ],
        )

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

    def test_git_fetch_with_external_version(self):
        """Test that fetching an external build (PR branch) correctly executes."""
        version = fixture.get(Version, project=self.project, type=EXTERNAL, active=True)
        repo = self.project.vcs_repo(
            verbose_name=version.verbose_name,
            version_type=version.type,
            environment=self.build_environment,
        )
        repo.update()
        code, _, _ = repo.fetch()
        self.assertEqual(code, 0)

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
@mock.patch("readthedocs.doc_builder.environments.BuildCommand.save", mock.MagicMock())
class TestHgBackend(TestCase):
    def setUp(self):
        hg_repo = make_test_hg()
        super().setUp()
        self.eric = User(username="eric")
        self.eric.set_password("test")
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="hg",
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
        version = "invalid-revision"
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
            ("aa1f3be38ab1", "1.8.1"),
            ("2616325766e3", "1.8"),
            ("2b2155623ee2", "1.7.5"),
        ]

        given_ids = [
            (x.identifier, x.verbose_name)
            for x in self.project.vcs_repo(
                environment=self.build_environment
            ).parse_tags(data)
        ]
        self.assertEqual(expected_tags, given_ids)
