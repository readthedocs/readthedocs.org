import os
import uuid
from unittest import mock
from unittest.mock import Mock, PropertyMock, patch

import pytest
from django.test import TestCase, override_settings
from django_dynamic_fixture import get
from docker.errors import APIError as DockerAPIError

from readthedocs.projects.models import APIProject
from readthedocs.builds.models import Version
from readthedocs.doc_builder.environments import (
    BuildCommand,
    DockerBuildCommand,
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.projects.models import Project

DUMMY_BUILD_ID = 123
SAMPLE_UNICODE = "HérÉ îß sömê ünïçó∂é"
SAMPLE_UTF8_BYTES = SAMPLE_UNICODE.encode("utf-8")


# TODO: these tests need to be re-written to make usage of the Celery handlers
# properly to check not recorded/recorded as success. For now, they are
# minimally updated to keep working, but they could be improved.
class TestLocalBuildEnvironment(TestCase):
    def test_command_not_recorded(self):
        api_client = mock.MagicMock()
        build_env = LocalBuildEnvironment(api_client=api_client)

        with build_env:
            build_env.run("true", record=False)
        self.assertEqual(len(build_env.commands), 0)
        api_client.command.post.assert_not_called()

    def test_record_command_as_success(self):
        api_client = mock.MagicMock()
        api_client.command().patch.return_value = {
            "id": 1,
        }
        project = APIProject(**get(Project).__dict__)
        build_env = LocalBuildEnvironment(
            project=project,
            build={
                "id": 1,
            },
            api_client=api_client,
        )

        with build_env:
            build_env.run(
                "false",
                record_as_success=True,
                # Use a directory that exists so the command doesn't fail.
                cwd="/tmp",
            )
        self.assertEqual(len(build_env.commands), 1)

        command = build_env.commands[0]
        assert command.exit_code == 0
        assert command.id == 1
        api_client.command.post.assert_called_once_with(
            {
                "build": mock.ANY,
                "command": command.get_command(),
                "output": "",
                "exit_code": None,
                "start_time": None,
                "end_time": None,
            }
        )
        api_client.command().patch.assert_called_once_with(
            {
                "build": mock.ANY,
                "command": command.get_command(),
                "output": command.output,
                "exit_code": 0,
                "start_time": command.start_time,
                "end_time": command.end_time,
            }
        )


# TODO: translate these tests into
# `readthedocs/projects/tests/test_docker_environment.py`. I've started the
# work there but it requires a good amount of work to mock it properly and
# reliably. I think we can skip these tests (3) for now since we are raising
# BuildAppError on these cases which we are already handling in other test
# cases.
#
# Once we mock the DockerBuildEnvironment properly, we could also translate the
# new tests from `readthedocs/projects/tests/test_build_tasks.py` to use this
# mocks.
@pytest.mark.skip
class TestDockerBuildEnvironment(TestCase):

    """Test docker build environment."""

    fixtures = ["test_data", "eric"]

    def setUp(self):
        self.project = Project.objects.get(slug="pip")
        self.version = Version(slug="foo", verbose_name="foobar")
        self.project.versions.add(self.version, bulk=False)

    def test_container_already_exists(self):
        """Docker container already exists."""
        self.mocks.configure_mock(
            "docker_client",
            {
                "inspect_container.return_value": {"State": {"Running": True}},
                "exec_create.return_value": {"Id": b"container-foobar"},
                "exec_start.return_value": b"This is the return",
                "exec_inspect.return_value": {"ExitCode": 0},
            },
        )

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={"id": DUMMY_BUILD_ID},
        )

        def _inner():
            with build_env:
                build_env.run("echo", "test", cwd="/tmp")

        self.assertRaises(BuildAppError, _inner)
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 0)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        # The build failed before executing any command
        self.assertFalse(self.mocks.mocks["api_v2.command"].post.called)
        self.mocks.mocks["api_v2.build"]().put.assert_called_with(
            {
                "id": DUMMY_BUILD_ID,
                "version": self.version.pk,
                "success": False,
                "project": self.project.pk,
                "setup_error": "",
                "exit_code": 1,
                "length": 0,
                "error": "A build environment is currently running for this version",
                "setup": "",
                "output": "",
                "state": "finished",
                "builder": mock.ANY,
            }
        )

    def test_container_timeout(self):
        """Docker container timeout and command failure."""
        response = Mock(status_code=404, reason="Container not found")
        self.mocks.configure_mock(
            "docker_client",
            {
                "inspect_container.side_effect": [
                    DockerAPIError(
                        "No container found",
                        response,
                        "No container found",
                    ),
                    {"State": {"Running": False, "ExitCode": 42}},
                ],
                "exec_create.return_value": {"Id": b"container-foobar"},
                "exec_start.return_value": b"This is the return",
                "exec_inspect.return_value": {"ExitCode": 0},
            },
        )

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={"id": DUMMY_BUILD_ID},
        )
        with build_env:
            build_env.run("echo", "test", cwd="/tmp")

        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        # The command was saved
        command = build_env.commands[0]
        self.mocks.mocks["api_v2.command"].post.assert_called_once_with(
            {
                "build": DUMMY_BUILD_ID,
                "command": command.get_command(),
                "description": command.description,
                "output": command.output,
                "exit_code": 0,
                "start_time": command.start_time,
                "end_time": command.end_time,
            }
        )
        self.mocks.mocks["api_v2.build"]().put.assert_called_with(
            {
                "id": DUMMY_BUILD_ID,
                "version": self.version.pk,
                "success": False,
                "project": self.project.pk,
                "setup_error": "",
                "exit_code": 1,
                "length": 0,
                "error": "Build exited due to time out",
                "setup": "",
                "output": "",
                "state": "finished",
                "builder": mock.ANY,
            }
        )


# NOTE: these tests should be migrated to not use `LocalBuildEnvironment`
# behind the scenes and mock the execution of the command itself by using
# `DockerBuildEnvironment`.
#
# They should be merged with the following test suite `TestDockerBuildCommand`.
#
# Also note that we require a Docker setting here for the tests to pass, but we
# are not using Docker at all.
@override_settings(RTD_DOCKER_WORKDIR="/tmp")
class TestBuildCommand(TestCase):

    """Test build command creation."""

    def test_command_env(self):
        """Test build command env vars."""
        env = {"FOOBAR": "foobar", "BIN_PATH": "foobar"}
        cmd = BuildCommand("echo", environment=env)
        for key in list(env.keys()):
            self.assertEqual(cmd._environment[key], env[key])

    def test_result(self):
        """Test result of output using unix true/false commands."""
        cmd = BuildCommand("true")
        cmd.run()
        self.assertTrue(cmd.successful)

        cmd = BuildCommand("false")
        cmd.run()
        self.assertTrue(cmd.failed)

    def test_missing_command(self):
        """Test missing command."""
        path = os.path.join("non-existant", str(uuid.uuid4()))
        self.assertFalse(os.path.exists(path))
        cmd = BuildCommand(path)
        cmd.run()
        self.assertEqual(cmd.exit_code, -1)
        # There is no stacktrace here.
        self.assertIsNone(cmd.output)
        self.assertIsNone(cmd.error)

    def test_output(self):
        """Test output command."""
        project = APIProject(**get(Project).__dict__)
        api_client = mock.MagicMock()
        build_env = LocalBuildEnvironment(
            project=project,
            build={
                "id": 1,
            },
            api_client=api_client,
        )
        cmd = BuildCommand(["/bin/bash", "-c", "echo -n FOOBAR"], build_env=build_env)

        # Mock BuildCommand.sanitized_output just to count the amount of calls,
        # but use the original method to behaves as real
        original_sanitized_output = cmd.sanitize_output
        with patch(
            "readthedocs.doc_builder.environments.BuildCommand.sanitize_output"
        ) as sanitize_output:  # noqa
            sanitize_output.side_effect = original_sanitized_output
            cmd.run()
            cmd.save(api_client=api_client)
            self.assertEqual(cmd.output, "FOOBAR")
            api_client.command.post.assert_called_once_with(
                {
                    "build": mock.ANY,
                    "command": "/bin/bash -c echo -n FOOBAR",
                    "output": "FOOBAR",
                    "exit_code": 0,
                    "start_time": mock.ANY,
                    "end_time": mock.ANY,
                }
            )

            # Check that we sanitize the output
            self.assertEqual(sanitize_output.call_count, 1)

    def test_error_output(self):
        """Test error output from command."""
        cmd = BuildCommand(["/bin/bash", "-c", "echo -n FOOBAR 1>&2"])
        cmd.run()
        self.assertEqual(cmd.output, "FOOBAR")
        self.assertEqual(cmd.error, "")

    def test_sanitize_output(self):
        cmd = BuildCommand(["/bin/bash", "-c", "echo"])
        checks = (
            ("Hola", "Hola"),
            ("H\x00i", "Hi"),
            ("H\x00i \x00\x00\x00You!\x00", "Hi You!"),
        )
        for output, sanitized in checks:
            self.assertEqual(cmd.sanitize_output(output), sanitized)

    def test_obfuscate_output_private_variables(self):
        build_env = mock.MagicMock()
        build_env.project = mock.MagicMock()
        build_env.project._environment_variables = mock.MagicMock()
        build_env.project._environment_variables.items.return_value = [
            (
                "PUBLIC",
                {
                    "public": True,
                    "value": "public-value",
                },
            ),
            (
                "PRIVATE",
                {
                    "public": False,
                    "value": "private-value",
                },
            ),
        ]
        cmd = BuildCommand(["/bin/bash", "-c", "echo"], build_env=build_env)
        checks = (
            ("public-value", "public-value"),
            ("private-value", "priv****"),
        )
        for output, sanitized in checks:
            self.assertEqual(cmd.sanitize_output(output), sanitized)

    @patch("subprocess.Popen")
    def test_unicode_output(self, mock_subprocess):
        """Unicode output from command."""
        mock_process = Mock(
            **{
                "communicate.return_value": (SAMPLE_UTF8_BYTES, b""),
            }
        )
        mock_subprocess.return_value = mock_process

        cmd = BuildCommand(["echo", "test"], cwd="/tmp/foobar")
        cmd.run()
        self.assertEqual(
            cmd.output,
            "H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9",
        )


# TODO: translate this tests once we have DockerBuildEnvironment properly
# mocked. These can be done together with `TestDockerBuildEnvironment`.
@pytest.mark.skip
class TestDockerBuildCommand(TestCase):

    """Test docker build commands."""

    def test_wrapped_command(self):
        """Test shell wrapping for Docker chdir."""
        cmd = DockerBuildCommand(
            ["pip", "install", "requests"],
            cwd="/tmp/foobar",
        )
        self.assertEqual(
            cmd.get_wrapped_command(),
            "/bin/sh -c 'pip install requests'",
        )
        cmd = DockerBuildCommand(
            ["python", "/tmp/foo/pip", "install", "Django>1.7"],
            cwd="/tmp/foobar",
            bin_path="/tmp/foo",
        )
        self.assertEqual(
            cmd.get_wrapped_command(),
            (
                "/bin/sh -c "
                "'PATH=/tmp/foo:$PATH "
                r"python /tmp/foo/pip install Django\>1.7'"
            ),
        )

    def test_unicode_output(self):
        """Unicode output from command."""
        self.mocks.configure_mock(
            "docker_client",
            {
                "exec_create.return_value": {"Id": b"container-foobar"},
                "exec_start.return_value": SAMPLE_UTF8_BYTES,
                "exec_inspect.return_value": {"ExitCode": 0},
            },
        )
        cmd = DockerBuildCommand(["echo", "test"], cwd="/tmp/foobar")
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value="foo")
        cmd.run()
        self.assertEqual(
            cmd.output,
            "H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9",
        )
        self.assertEqual(self.mocks.docker_client.exec_start.call_count, 1)
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)
        self.assertEqual(self.mocks.docker_client.exec_inspect.call_count, 1)

    def test_command_oom_kill(self):
        """Command is OOM killed."""
        self.mocks.configure_mock(
            "docker_client",
            {
                "exec_create.return_value": {"Id": b"container-foobar"},
                "exec_start.return_value": b"Killed\n",
                "exec_inspect.return_value": {"ExitCode": 137},
            },
        )
        cmd = DockerBuildCommand(["echo", "test"], cwd="/tmp/foobar")
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value="foo")
        cmd.run()
        self.assertIn(
            "Command killed due to timeout or excessive memory consumption\n",
            str(cmd.output),
        )
