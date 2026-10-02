import os
import shlex
import subprocess
import tempfile

from django.test import TestCase

from readthedocs.doc_builder.environments import DockerBuildCommand


def docker_argv(wrapped_command):
    """
    Build the container argv the same way ``docker-py`` does.

    ``APIClient.exec_create()`` calls ``docker.utils.split_command()`` on a
    string ``cmd``, and that function is ``shlex.split()``.
    """
    return shlex.split(wrapped_command)


def shell_script(wrapped_command):
    """Return the script ``/bin/sh -c`` receives, as the container would see it."""
    argv = docker_argv(wrapped_command)
    assert argv[:5] == ["nice", "-n", "10", "/bin/sh", "-c"], argv
    assert len(argv) == 6, argv
    return argv[5]


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

    def test_command_with_single_quote_is_splittable(self):
        """
        A single quote in an argument must not break ``shlex.split()``.

        ``extractbb`` is run once per image found in the LaTeX output
        directory, so the filename is whatever the user committed.
        """
        commands = [
            (["extractbb", "Gino's.png"], "extractbb Gino\\'s.png"),
            (
                ["extractbb", "exemple_d'une_mise_à_jour.png"],
                "extractbb exemple_d\\'une_mise_à_jour.png",
            ),
            (["extractbb", "a'b'c.png"], "extractbb a\\'b\\'c.png"),
            (["extractbb", "Gino's diagram.png"], "extractbb Gino\\'s\\ diagram.png"),
            (["extractbb", "'"], "extractbb \\'"),
        ]
        for command, expected in commands:
            build_command = DockerBuildCommand(command=command)
            # Raises ValueError("No closing quotation") when the script is
            # hand-wrapped in `'...'`.
            assert shell_script(build_command.get_wrapped_command()) == expected, command

    def test_unescaped_command_reaches_the_shell_unchanged(self):
        """
        ``escape_command=False`` commands are user shell snippets.

        These come from ``build.jobs`` and ``build.commands`` in the user's
        configuration file, and are meant to be interpreted by the shell
        exactly as written.
        """
        commands = [
            "sed -i 's/foo/bar/' docs/conf.py",
            "echo 'two words' > docs/version.txt",
            "python -c 'import sys; print(sys.version)'",
            "asdf reshim python",
            'echo "no single quotes here"',
        ]
        for command in commands:
            build_command = DockerBuildCommand(
                command=[command],
                escape_command=False,
            )
            assert shell_script(build_command.get_wrapped_command()) == command, command

    def test_bin_path_prefix_with_single_quote(self):
        build_command = DockerBuildCommand(
            command=["extractbb", "Gino's.png"],
            bin_path="/tmp/foo",
        )
        assert (
            shell_script(build_command.get_wrapped_command())
            == "PATH=/tmp/foo:$PATH ; extractbb Gino\\'s.png"
        )

    def test_not_escaped_variables_still_expand(self):
        build_command = DockerBuildCommand(
            command=["mkdir", "-p", "$READTHEDOCS_OUTPUT/html", "a'b"],
        )
        assert (
            shell_script(build_command.get_wrapped_command())
            == "mkdir -p $READTHEDOCS_OUTPUT/html a\\'b"
        )

    def test_wrapped_command_runs_with_the_intended_argv(self):
        """
        End to end: the program inside the container gets the right argv.

        ``printf '[%s]' a b`` prints ``[a][b]``, so a lost quote, a dropped
        argument and a wrongly split one all look different in the output.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            marker = os.path.join(tmpdir, "injected")
            cases = [
                (["printf", "[%s]", "Gino's.png"], "[Gino's.png]"),
                (["printf", "[%s]", "a b", "c'd"], "[a b][c'd]"),
                (["printf", "[%s]", f"; touch {marker}"], f"[; touch {marker}]"),
                (["printf", "[%s]", "$HOME"], "[$HOME]"),
                (["printf", "[%s]", f"'; touch {marker}; '"], f"['; touch {marker}; ']"),
                (["printf", "[%s]", f"$(touch {marker})"], f"[$(touch {marker})]"),
            ]
            for command, expected in cases:
                script = shell_script(DockerBuildCommand(command=command).get_wrapped_command())
                result = subprocess.run(
                    ["/bin/sh", "-c", script],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                assert result.stdout == expected, command
                assert not os.path.exists(marker), command
