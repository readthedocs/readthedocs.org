from types import SimpleNamespace
from unittest import mock

from django.test import TestCase
from django.test import override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Build
from readthedocs.doc_builder.director import BuildDirector
from readthedocs.projects.models import Project


class TestBuildDirectorEnvironmentVariables(TestCase):
    """Test environment variables set by BuildDirector."""

    def setUp(self):
        self.project = get(Project, slug="test-project")
        self.version = self.project.versions.get(slug="latest")
        self.build = get(
            Build,
            project=self.project,
            version=self.version,
            commit="abc123",
        )

        # Required since it's a APIVersion behind the scenes
        self.version.canonical_url = "https://test-project.readthedocs.io/en/latest/"

        # Create a minimal data object that BuildDirector expects
        self.data = mock.Mock()
        self.data.project = self.project
        self.data.version = self.version
        self.data.build = {"commit": "abc123"}
        self.data.config = mock.Mock()
        self.data.config.conda = None

        self.director = BuildDirector(self.data)

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_git_ssh_command_set_when_private_repos_enabled(self):
        """Test that GIT_SSH_COMMAND is set when ALLOW_PRIVATE_REPOS is True."""
        env_vars = self.director.get_build_env_vars()
        self.assertIn("GIT_SSH_COMMAND", env_vars)
        # Verify it contains the ssh command with proper options
        self.assertEqual(
            env_vars["GIT_SSH_COMMAND"],
            "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
        )

        env_vars = self.director.get_vcs_env_vars()
        self.assertIn("GIT_SSH_COMMAND", env_vars)
        # Verify it contains the ssh command with proper options
        self.assertEqual(
            env_vars["GIT_SSH_COMMAND"],
            "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
        )

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_git_ssh_command_not_set_when_private_repos_disabled(self):
        """Test that GIT_SSH_COMMAND is not set when ALLOW_PRIVATE_REPOS is False."""
        env_vars = self.director.get_build_env_vars()
        self.assertNotIn("GIT_SSH_COMMAND", env_vars)

        env_vars = self.director.get_vcs_env_vars()
        self.assertNotIn("GIT_SSH_COMMAND", env_vars)


class TestBuildDirectorBuildJobTracking(TestCase):
    def setUp(self):
        self.data = mock.Mock()
        self.data.project = mock.Mock()
        self.data.project.checkout_path.return_value = "/tmp/project"
        self.data.project.doc_path = "/tmp/project"
        self.data.version = mock.Mock()
        self.data.version.slug = "latest"
        self.data.version.type = "branch"
        self.data.build = {"id": 1}
        self.data.api_client = mock.Mock()

        build_jobs = SimpleNamespace(
            pre_system_dependencies=None,
            post_system_dependencies=None,
            pre_create_environment=None,
            post_create_environment=None,
            pre_install=None,
            post_install=None,
            create_environment=None,
            install=None,
            build=SimpleNamespace(html=None, pdf=None, htmlzip=None, epub=None),
        )

        self.data.config = SimpleNamespace(
            build=SimpleNamespace(
                jobs=build_jobs,
                apt_packages=["curl"],
                commands=["echo hello"],
                tools={},
                os="ubuntu-22.04",
            ),
            doctype="sphinx",
            formats=["pdf", "epub", "htmlzip"],
            python_interpreter="python",
            is_using_setup_py_install=False,
            is_using_conda=False,
        )

        self.director = BuildDirector(self.data)
        self.director.build_environment = mock.Mock()
        self.director.build_environment.build_job = None

    @mock.patch("readthedocs.doc_builder.director.Virtualenv")
    def test_setup_environment_sets_build_job(self, virtualenv):
        captured_jobs = []
        virtualenv.return_value = mock.Mock()

        self.director.system_dependencies = mock.Mock(
            side_effect=lambda: captured_jobs.append(self.director.build_environment.build_job)
        )
        self.director.install_build_tools = mock.Mock(
            side_effect=lambda: captured_jobs.append(self.director.build_environment.build_job)
        )
        self.director.create_environment = mock.Mock(
            side_effect=lambda: captured_jobs.append(self.director.build_environment.build_job)
        )
        self.director.install = mock.Mock(
            side_effect=lambda: captured_jobs.append(self.director.build_environment.build_job)
        )

        self.director.setup_environment()

        self.assertEqual(
            captured_jobs,
            [
                "system_dependencies",
                "install_build_tools",
                "create_environment",
                "install",
            ],
        )
        self.assertIsNone(self.director.build_environment.build_job)

    def test_build_html_default_sets_build_job(self):
        captured_jobs = []

        def build_docs_class_side_effect(*args, **kwargs):
            captured_jobs.append(self.director.build_environment.build_job)
            return True

        self.director.build_docs_class = mock.Mock(side_effect=build_docs_class_side_effect)

        self.assertTrue(self.director.build_html())
        self.assertEqual(captured_jobs, ["build.html"])
        self.assertIsNone(self.director.build_environment.build_job)

    def test_run_build_commands_sets_build_job(self):
        captured_jobs = []

        def run_side_effect(*args, **kwargs):
            captured_jobs.append(self.director.build_environment.build_job)
            return mock.Mock()

        self.director.build_environment.run.side_effect = run_side_effect
        self.director.store_readthedocs_build_yaml = mock.Mock()
        with mock.patch("readthedocs.doc_builder.director.os.path.exists", return_value=True):
            self.director.run_build_commands()

        self.assertEqual(captured_jobs, ["build.commands"])
        self.assertIsNone(self.director.build_environment.build_job)
