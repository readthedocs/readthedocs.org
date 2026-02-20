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


class TestBuildDirectorJobMetadata(TestCase):
    @override_settings(ALLOW_PRIVATE_REPOS=False)
    @mock.patch("readthedocs.doc_builder.director.load_yaml_config")
    @mock.patch("readthedocs.doc_builder.director.find_one")
    def test_checkout_sets_checkout_job_context(self, find_one, load_yaml_config):
        data = mock.Mock()
        data.project = mock.Mock()
        data.project.default_branch = "main"
        data.project.readthedocs_yaml_path = None
        data.project.checkout_path.return_value = "/tmp/repo"
        data.version = mock.Mock()
        data.version.slug = "latest"
        data.version.identifier = "main"
        data.version.is_machine_latest = False
        data.version.project = mock.Mock(readthedocs_yaml_path=None)
        data.build = {}
        data.build_commit = None

        director = BuildDirector(data)
        director.vcs_environment = mock.Mock(build_job=None)
        director.vcs_repository = mock.Mock()
        director.vcs_repository.has_ssh_key_with_write_access.return_value = False

        config = mock.Mock()
        config.version = 2
        config.source_config = {"build": {"os": "ubuntu-24.04"}}
        config.as_dict.return_value = {"build": {"os": "ubuntu-24.04"}}

        find_one.return_value = None
        load_yaml_config.return_value = config
        director.checkout()
        self.assertEqual(director.vcs_environment.build_job, "checkout")

    @override_settings(RTD_DOCKER_COMPOSE=False)
    @mock.patch("readthedocs.doc_builder.director.get_storage")
    @mock.patch("readthedocs.doc_builder.director.Virtualenv")
    def test_setup_environment_sets_predefined_job_context(self, virtualenv_cls, get_storage):
        data = mock.Mock()
        data.project = mock.Mock()
        data.project.checkout_path.return_value = "/tmp/repo"
        data.project.doc_path = "/tmp/docs"
        data.version = mock.Mock()
        data.version.slug = "latest"
        data.version.is_external = False
        data.api_client = mock.Mock()
        data.build = {"id": 1}
        data.config = SimpleNamespace(
            is_using_conda=False,
            doctype="generic",
            build=SimpleNamespace(
                os="ubuntu-24.04",
                apt_packages=[],
                tools={},
                jobs=SimpleNamespace(
                    pre_system_dependencies=None,
                    post_system_dependencies=None,
                    pre_create_environment=None,
                    create_environment=None,
                    post_create_environment=None,
                    pre_install=None,
                    install=None,
                    post_install=None,
                ),
            ),
        )

        director = BuildDirector(data)
        director.build_environment = mock.Mock(build_job=None)
        director.vcs_environment = mock.Mock(build_job=None)
        virtualenv_cls.return_value = mock.Mock()
        get_storage.return_value = mock.Mock()

        captured = []
        original_system_dependencies = director.system_dependencies
        original_install_build_tools = director.install_build_tools
        original_create_environment = director.create_environment
        original_install = director.install

        def wrapped_system_dependencies():
            original_system_dependencies()
            captured.append(director.build_environment.build_job)

        def wrapped_install_build_tools():
            original_install_build_tools()
            captured.append(director.build_environment.build_job)

        def wrapped_create_environment():
            original_create_environment()
            captured.append(director.build_environment.build_job)

        def wrapped_install():
            original_install()
            captured.append(director.build_environment.build_job)

        director.system_dependencies = wrapped_system_dependencies
        director.install_build_tools = wrapped_install_build_tools
        director.create_environment = wrapped_create_environment
        director.install = wrapped_install

        director.setup_environment()

        self.assertEqual(
            captured,
            [
                "system_dependencies",
                "system_dependencies",
                "create_environment",
                "install",
            ],
        )
        self.assertEqual(director.build_environment.build_job, "install")

    def test_build_sets_predefined_build_step_context(self):
        data = mock.Mock()
        data.version = mock.Mock(type="branch")
        data.config = SimpleNamespace(
            doctype="sphinx",
            formats=["pdf", "htmlzip", "epub"],
            build=SimpleNamespace(
                jobs=SimpleNamespace(
                    pre_build=None,
                    post_build=None,
                    build=SimpleNamespace(
                        html=None,
                        pdf=None,
                        htmlzip=None,
                        epub=None,
                    ),
                ),
            ),
        )

        director = BuildDirector(data)
        director.build_environment = mock.Mock(build_job=None)
        director.run_build_job = mock.Mock()
        director.store_readthedocs_build_yaml = mock.Mock()

        captured = []
        director.build_docs_class = mock.Mock(
            side_effect=lambda _builder: captured.append(director.build_environment.build_job)
        )

        director.build()

        self.assertEqual(
            captured,
            [
                "build",
                "build",
                "build",
                "build",
            ],
        )
        self.assertEqual(director.build_environment.build_job, "build")

    def test_run_build_job_uses_existing_step_context(self):
        data = mock.Mock()
        data.project = mock.Mock()
        data.project.checkout_path.return_value = "/tmp/repo"
        data.version = mock.Mock()
        data.version.slug = "latest"
        data.config = SimpleNamespace(
            build=SimpleNamespace(
                jobs=SimpleNamespace(
                    pre_install=["echo pre install"],
                    post_checkout=["echo post checkout"],
                    build=SimpleNamespace(html=["echo build html"]),
                ),
            ),
        )

        director = BuildDirector(data)
        director.vcs_environment = mock.Mock(build_job="checkout")
        director.build_environment = mock.Mock(build_job="install")

        director.run_build_job("pre_install")
        self.assertEqual(director.build_environment.build_job, "install")
        director.build_environment.run.assert_called_once_with(
            "echo pre install",
            escape_command=False,
            cwd="/tmp/repo",
        )

        director.run_build_job("post_checkout")
        self.assertEqual(director.vcs_environment.build_job, "checkout")
        director.vcs_environment.run.assert_called_once_with(
            "echo post checkout",
            escape_command=False,
            cwd="/tmp/repo",
        )

        director.build_environment.build_job = "build"
        director.run_build_job("build.html")
        self.assertEqual(director.build_environment.build_job, "build")
        director.build_environment.run.assert_any_call(
            "echo build html",
            escape_command=False,
            cwd="/tmp/repo",
        )
