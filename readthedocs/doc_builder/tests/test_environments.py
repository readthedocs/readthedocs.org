import datetime
from unittest import mock

from django.test import TestCase

from readthedocs.doc_builder.environments import BuildCommand
from readthedocs.doc_builder.environments import DockerBuildCommand
from readthedocs.doc_builder.environments import LocalBuildEnvironment


class TestDockerBuildEnvironment(TestCase):
    def test_command_escape(self):
        commands = [
            (
                ["ls", ".", "; touch /tmp/test"],
                "nice -n 10 /bin/sh -c 'ls . \\;\\ touch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ntouch /tmp/test"],
                "nice -n 10 /bin/sh -c 'ls . \\\ntouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ftouch /tmp/test"],
                "nice -n 10 /bin/sh -c 'ls . \\\ftouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ttouch /tmp/test"],
                "nice -n 10 /bin/sh -c 'ls . \\\ttouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\vtouch /tmp/test"],
                "nice -n 10 /bin/sh -c 'ls . \\\vtouch\\ /tmp/test'",
            ),
        ]
        for command, expected in commands:
            build_command = DockerBuildCommand(command=command)
            assert build_command.get_wrapped_command() == expected, command

    def test_build_job_is_sent_in_command_payload(self):
        api_client = mock.MagicMock()
        api_client.command.post.return_value = {"id": 1}
        project = mock.MagicMock()
        project._environment_variables = {}

        build_environment = LocalBuildEnvironment(
            project=project,
            build={"id": 42},
            api_client=api_client,
        )
        build_environment.build_job = "install"

        class _SuccessfulBuildCommand(BuildCommand):
            def run(self):
                self.start_time = datetime.datetime.utcnow()
                self.end_time = datetime.datetime.utcnow()
                self.exit_code = 0
                self.output = ""

        build_environment.run_command_class(
            cls=_SuccessfulBuildCommand,
            cmd=("echo", "hello"),
        )

        command_data = api_client.command.post.call_args.args[0]
        assert command_data["job"] == "install"
