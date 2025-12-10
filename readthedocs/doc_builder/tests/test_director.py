from unittest import mock

from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.builds.models import Build, Version
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

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_git_ssh_command_not_set_when_private_repos_disabled(self):
        """Test that GIT_SSH_COMMAND is not set when ALLOW_PRIVATE_REPOS is False."""
        env_vars = self.director.get_build_env_vars()
        self.assertNotIn("GIT_SSH_COMMAND", env_vars)
