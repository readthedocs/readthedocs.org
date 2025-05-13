from django.test import TestCase

from readthedocs.doc_builder.environments import DockerBuildCommand


class TestDockerBuildEnvironment(TestCase):
    def test_command_escape(self):
        commands = [
            (
                ["ls", ".", "; touch /tmp/test"],
                "/bin/sh -c 'ls . \\;\\ touch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ntouch /tmp/test"],
                "/bin/sh -c 'ls . \\\ntouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ftouch /tmp/test"],
                "/bin/sh -c 'ls . \\\ftouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\ttouch /tmp/test"],
                "/bin/sh -c 'ls . \\\ttouch\\ /tmp/test'",
            ),
            (
                ["ls", ".", "\vtouch /tmp/test"],
                "/bin/sh -c 'ls . \\\vtouch\\ /tmp/test'",
            ),
        ]
        for command, expected in commands:
            build_command = DockerBuildCommand(command=command)
            assert build_command.get_wrapped_command() == expected, command
