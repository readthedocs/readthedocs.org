import os
import tempfile
import uuid
from itertools import zip_longest
from unittest import mock
from unittest.mock import Mock, PropertyMock, patch

import pytest
from django.test import TestCase, override_settings
from django_dynamic_fixture import get
from docker.errors import APIError as DockerAPIError

from readthedocs.builds.models import Version
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import (
    BuildCommand,
    DockerBuildCommand,
    DockerBuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.mocks.paths import fake_paths_lookup
from readthedocs.rtd_tests.tests.test_config_integration import create_load

DUMMY_BUILD_ID = 123
SAMPLE_UNICODE = 'HérÉ îß sömê ünïçó∂é'
SAMPLE_UTF8_BYTES = SAMPLE_UNICODE.encode('utf-8')


# TODO: these tests need to be re-written to make usage of the Celery handlers
# properly to check not recorded/recorded as success. For now, they are
# minimally updated to keep working, but they could be improved.
class TestLocalBuildEnvironment(TestCase):


    @patch('readthedocs.doc_builder.environments.api_v2')
    def test_command_not_recorded(self, api_v2):
        build_env = LocalBuildEnvironment()

        with build_env:
            build_env.run('true', record=False)
        self.assertEqual(len(build_env.commands), 0)
        api_v2.command.post.assert_not_called()

    @patch('readthedocs.doc_builder.environments.api_v2')
    def test_record_command_as_success(self, api_v2):
        project = get(Project)
        build_env = LocalBuildEnvironment(
            project=project,
            build={
                'id': 1,
            },
        )

        with build_env:
            build_env.run('false', record_as_success=True)
        self.assertEqual(len(build_env.commands), 1)

        command = build_env.commands[0]
        self.assertEqual(command.exit_code, 0)
        api_v2.command.post.assert_called_once_with({
            'build': mock.ANY,
            'command': command.get_command(),
            'output': command.output,
            'exit_code': 0,
            'start_time': command.start_time,
            'end_time': command.end_time,
        })



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

    fixtures = ['test_data', 'eric']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version, bulk=False)

    def test_container_already_exists(self):
        """Docker container already exists."""
        self.mocks.configure_mock(
            'docker_client', {
                'inspect_container.return_value': {'State': {'Running': True}},
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'This is the return',
                'exec_inspect.return_value': {'ExitCode': 0},
            },
        )

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        def _inner():
            with build_env:
                build_env.run('echo', 'test', cwd='/tmp')

        self.assertRaises(BuildAppError, _inner)
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 0)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        # The build failed before executing any command
        self.assertFalse(self.mocks.mocks['api_v2.command'].post.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': '',
            'exit_code': 1,
            'length': 0,
            'error': 'A build environment is currently running for this version',
            'setup': '',
            'output': '',
            'state': 'finished',
            'builder': mock.ANY,
        })

    def test_container_timeout(self):
        """Docker container timeout and command failure."""
        response = Mock(status_code=404, reason='Container not found')
        self.mocks.configure_mock(
            'docker_client', {
                'inspect_container.side_effect': [
                    DockerAPIError(
                        'No container found',
                        response,
                        'No container found',
                    ),
                    {'State': {'Running': False, 'ExitCode': 42}},
                ],
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'This is the return',
                'exec_inspect.return_value': {'ExitCode': 0},
            },
        )

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        # The command was saved
        command = build_env.commands[0]
        self.mocks.mocks['api_v2.command'].post.assert_called_once_with({
            'build': DUMMY_BUILD_ID,
            'command': command.get_command(),
            'description': command.description,
            'output': command.output,
            'exit_code': 0,
            'start_time': command.start_time,
            'end_time': command.end_time,
        })
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': '',
            'exit_code': 1,
            'length': 0,
            'error': 'Build exited due to time out',
            'setup': '',
            'output': '',
            'state': 'finished',
            'builder': mock.ANY,
        })


# NOTE: these tests should be migrated to not use `LocalBuildEnvironment`
# behind the scenes and mock the execution of the command itself by using
# `DockerBuildEnvironment`.
#
# They should be merged with the following test suite `TestDockerBuildCommand`.
#
# Also note that we require a Docker setting here for the tests to pass, but we
# are not using Docker at all.
@override_settings(RTD_DOCKER_WORKDIR='/tmp')
class TestBuildCommand(TestCase):

    """Test build command creation."""

    def test_command_env(self):
        """Test build command env vars."""
        env = {'FOOBAR': 'foobar', 'BIN_PATH': 'foobar'}
        cmd = BuildCommand('echo', environment=env)
        for key in list(env.keys()):
            self.assertEqual(cmd._environment[key], env[key])

    def test_result(self):
        """Test result of output using unix true/false commands."""
        cmd = BuildCommand('true')
        cmd.run()
        self.assertTrue(cmd.successful)

        cmd = BuildCommand('false')
        cmd.run()
        self.assertTrue(cmd.failed)

    def test_missing_command(self):
        """Test missing command."""
        path = os.path.join('non-existant', str(uuid.uuid4()))
        self.assertFalse(os.path.exists(path))
        cmd = BuildCommand(path)
        cmd.run()
        self.assertEqual(cmd.exit_code, -1)
        # There is no stacktrace here.
        self.assertIsNone(cmd.output)
        self.assertIsNone(cmd.error)

    def test_output(self):
        """Test output command."""
        cmd = BuildCommand(['/bin/bash', '-c', 'echo -n FOOBAR'])

        # Mock BuildCommand.sanitized_output just to count the amount of calls,
        # but use the original method to behaves as real
        original_sanitized_output = cmd.sanitize_output
        with patch('readthedocs.doc_builder.environments.BuildCommand.sanitize_output') as sanitize_output:  # noqa
            sanitize_output.side_effect = original_sanitized_output
            cmd.run()
            self.assertEqual(cmd.output, 'FOOBAR')

            # Check that we sanitize the output
            self.assertEqual(sanitize_output.call_count, 2)

    def test_error_output(self):
        """Test error output from command."""
        cmd = BuildCommand(['/bin/bash', '-c', 'echo -n FOOBAR 1>&2'])
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')
        self.assertEqual(cmd.error, "")

    def test_sanitize_output(self):
        cmd = BuildCommand(['/bin/bash', '-c', 'echo'])
        checks = (
            (b'Hola', 'Hola'),
            (b'H\x00i', 'Hi'),
            (b'H\x00i \x00\x00\x00You!\x00', 'Hi You!'),
        )
        for output, sanitized in checks:
            self.assertEqual(cmd.sanitize_output(output), sanitized)

    @patch('subprocess.Popen')
    def test_unicode_output(self, mock_subprocess):
        """Unicode output from command."""
        mock_process = Mock(**{
            'communicate.return_value': (SAMPLE_UTF8_BYTES, b''),
        })
        mock_subprocess.return_value = mock_process

        cmd = BuildCommand(['echo', 'test'], cwd='/tmp/foobar')
        cmd.run()
        self.assertEqual(
            cmd.output,
            'H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9',
        )


# TODO: translate this tests once we have DockerBuildEnvironment properly
# mocked. These can be done together with `TestDockerBuildEnvironment`.
@pytest.mark.skip
class TestDockerBuildCommand(TestCase):

    """Test docker build commands."""

    def test_wrapped_command(self):
        """Test shell wrapping for Docker chdir."""
        cmd = DockerBuildCommand(
            ['pip', 'install', 'requests'],
            cwd='/tmp/foobar',
        )
        self.assertEqual(
            cmd.get_wrapped_command(),
            "/bin/sh -c 'pip install requests'",
        )
        cmd = DockerBuildCommand(
            ['python', '/tmp/foo/pip', 'install', 'Django>1.7'],
            cwd='/tmp/foobar',
            bin_path='/tmp/foo',
        )
        self.assertEqual(
            cmd.get_wrapped_command(),
            (
                '/bin/sh -c '
                "'PATH=/tmp/foo:$PATH "
                r"python /tmp/foo/pip install Django\>1.7'"
            ),
        )

    def test_unicode_output(self):
        """Unicode output from command."""
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': SAMPLE_UTF8_BYTES,
                'exec_inspect.return_value': {'ExitCode': 0},
            },
        )
        cmd = DockerBuildCommand(['echo', 'test'], cwd='/tmp/foobar')
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value='foo')
        cmd.run()
        self.assertEqual(
            cmd.output,
            'H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9',
        )
        self.assertEqual(self.mocks.docker_client.exec_start.call_count, 1)
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)
        self.assertEqual(self.mocks.docker_client.exec_inspect.call_count, 1)

    def test_command_oom_kill(self):
        """Command is OOM killed."""
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'Killed\n',
                'exec_inspect.return_value': {'ExitCode': 137},
            },
        )
        cmd = DockerBuildCommand(['echo', 'test'], cwd='/tmp/foobar')
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value='foo')
        cmd.run()
        self.assertIn(
            'Command killed due to timeout or excessive memory consumption\n',
            str(cmd.output),
        )


class TestPythonEnvironment(TestCase):

    def setUp(self):
        self.project_sphinx = get(Project, documentation_type='sphinx')
        self.version_sphinx = get(Version, project=self.project_sphinx)

        self.project_mkdocs = get(Project, documentation_type='mkdocs')
        self.version_mkdocs = get(Version, project=self.project_mkdocs)

        self.build_env_mock = Mock()

        self.base_requirements = [
            "pillow",
            "mock",
            "alabaster",
        ]
        self.base_conda_requirements = [
            'mock',
            'pillow',
        ]

        self.pip_install_args = [
            mock.ANY,  # python path
            '-m',
            'pip',
            'install',
            '--upgrade',
            '--no-cache-dir',
        ]

    def assertArgsStartsWith(self, args, call):
        """
        Assert that each element of args of the mock start
        with each element of args.
        """
        args_mock, _ = call
        for arg, arg_mock in zip_longest(args, args_mock):
            if arg is not mock.ANY:
                self.assertIsNotNone(arg_mock)
                self.assertTrue(arg_mock.startswith(arg), arg)

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_core_requirements_sphinx(self, checkout_path):
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Virtualenv(
            version=self.version_sphinx,
            build_env=self.build_env_mock,
        )
        python_env.install_core_requirements()
        requirements_sphinx = [
            "commonmark",
            "recommonmark",
            "sphinx",
            "sphinx-rtd-theme",
            "readthedocs-sphinx-ext",
            "jinja2<3.1.0",
        ]

        self.assertEqual(self.build_env_mock.run.call_count, 2)
        calls = self.build_env_mock.run.call_args_list

        core_args = self.pip_install_args + ['pip', 'setuptools<58.3.0']
        self.assertArgsStartsWith(core_args, calls[0])

        requirements = self.base_requirements + requirements_sphinx
        args = self.pip_install_args + requirements
        self.assertArgsStartsWith(args, calls[1])

    @mock.patch('readthedocs.doc_builder.config.load_config')
    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_core_requirements_sphinx_system_packages_caps_setuptools(self, checkout_path, load_config):
        config_data = {
            'python': {
                'use_system_site_packages': True,
            },
        }
        load_config.side_effect = create_load(config_data)
        config = load_yaml_config(self.version_sphinx)

        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Virtualenv(
            version=self.version_sphinx,
            build_env=self.build_env_mock,
            config=config,
        )
        python_env.install_core_requirements()
        requirements_sphinx = [
            "commonmark",
            "recommonmark",
            "sphinx",
            "sphinx-rtd-theme",
            "readthedocs-sphinx-ext",
            "jinja2<3.1.0",
            "setuptools<58.3.0",
        ]

        self.assertEqual(self.build_env_mock.run.call_count, 2)
        calls = self.build_env_mock.run.call_args_list

        core_args = self.pip_install_args + ['pip', 'setuptools<58.3.0']
        self.assertArgsStartsWith(core_args, calls[0])

        requirements = self.base_requirements + requirements_sphinx
        args = self.pip_install_args + ['-I'] + requirements
        self.assertArgsStartsWith(args, calls[1])

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_core_requirements_mkdocs(self, checkout_path):
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Virtualenv(
            version=self.version_mkdocs,
            build_env=self.build_env_mock,
        )
        python_env.install_core_requirements()
        requirements_mkdocs = [
            'commonmark',
            'recommonmark',
            'mkdocs',
        ]

        self.assertEqual(self.build_env_mock.run.call_count, 2)
        calls = self.build_env_mock.run.call_args_list

        core_args = self.pip_install_args + ['pip', 'setuptools<58.3.0']
        self.assertArgsStartsWith(core_args, calls[0])

        requirements = self.base_requirements + requirements_mkdocs
        args = self.pip_install_args + requirements
        self.assertArgsStartsWith(args, calls[1])

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_user_requirements(self, checkout_path):
        """
        If a projects does not specify a requirements file,
        RTD will choose one automatically.

        First by searching under the docs/ directory and then under the root.
        The files can be named as:

        - ``pip_requirements.txt``
        - ``requirements.txt``
        """
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        self.build_env_mock.project = self.project_sphinx
        self.build_env_mock.version = self.version_sphinx
        python_env = Virtualenv(
            version=self.version_sphinx,
            build_env=self.build_env_mock,
        )

        checkout_path = python_env.checkout_path
        docs_requirements = os.path.join(
            checkout_path, 'docs', 'requirements.txt',
        )
        root_requirements = os.path.join(
            checkout_path, 'requirements.txt',
        )
        paths = {
            os.path.join(checkout_path, 'docs'): True,
        }
        args = [
            mock.ANY,  # python path
            '-m',
            'pip',
            'install',
            '--exists-action=w',
            '--no-cache-dir',
            '-r',
            'requirements_file',
        ]

        # One requirements file on the docs/ dir
        # should be installed
        paths[docs_requirements] = True
        paths[root_requirements] = False
        with fake_paths_lookup(paths):
            python_env.install_requirements()
        args[-1] = 'docs/requirements.txt'
        self.build_env_mock.run.assert_called_with(
            *args, cwd=mock.ANY, bin_path=mock.ANY
        )

        # One requirements file on the root dir
        # should be installed
        paths[docs_requirements] = False
        paths[root_requirements] = True
        with fake_paths_lookup(paths):
            python_env.install_requirements()
        args[-1] = 'requirements.txt'
        self.build_env_mock.run.assert_called_with(
            *args, cwd=mock.ANY, bin_path=mock.ANY
        )

        # Two requirements files on the root and  docs/ dirs
        # the one on docs/ should be installed
        paths[docs_requirements] = True
        paths[root_requirements] = True
        with fake_paths_lookup(paths):
            python_env.install_requirements()
        args[-1] = 'docs/requirements.txt'
        self.build_env_mock.run.assert_called_with(
            *args, cwd=mock.ANY, bin_path=mock.ANY
        )

        # No requirements file
        # no requirements should be installed
        self.build_env_mock.run.reset_mock()
        paths[docs_requirements] = False
        paths[root_requirements] = False
        with fake_paths_lookup(paths):
            python_env.install_requirements()
        self.build_env_mock.run.assert_not_called()

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_core_requirements_sphinx_conda(self, checkout_path):
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Conda(
            version=self.version_sphinx,
            build_env=self.build_env_mock,
        )
        python_env.install_core_requirements()
        conda_sphinx = [
            'sphinx',
            'sphinx_rtd_theme',
        ]
        conda_requirements = self.base_conda_requirements + conda_sphinx
        pip_requirements = [
            'recommonmark',
            'readthedocs-sphinx-ext',
        ]

        args_pip = [
            mock.ANY,  # python path
            '-m',
            'pip',
            'install',
            '-U',
            '--no-cache-dir',
        ]
        args_pip.extend(pip_requirements)

        args_conda = [
            'conda',
            'install',
            '--yes',
            '--quiet',
            '--name',
            self.version_sphinx.slug,
        ]
        args_conda.extend(conda_requirements)

        self.build_env_mock.run.assert_has_calls([
            mock.call(*args_conda, cwd=mock.ANY),
            mock.call(*args_pip, bin_path=mock.ANY, cwd=mock.ANY),
        ])

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_core_requirements_mkdocs_conda(self, checkout_path):
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Conda(
            version=self.version_mkdocs,
            build_env=self.build_env_mock,
        )
        python_env.install_core_requirements()
        conda_requirements = self.base_conda_requirements
        pip_requirements = [
            'recommonmark',
            'mkdocs',
        ]

        args_pip = [
            mock.ANY,  # python path
            '-m',
            'pip',
            'install',
            '-U',
            '--no-cache-dir',
        ]
        args_pip.extend(pip_requirements)

        args_conda = [
            'conda',
            'install',
            '--yes',
            '--quiet',
            '--name',
            self.version_mkdocs.slug,
        ]
        args_conda.extend(conda_requirements)

        self.build_env_mock.run.assert_has_calls([
            mock.call(*args_conda, cwd=mock.ANY),
            mock.call(*args_pip, bin_path=mock.ANY, cwd=mock.ANY),
        ])

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_install_user_requirements_conda(self, checkout_path):
        tmpdir = tempfile.mkdtemp()
        checkout_path.return_value = tmpdir
        python_env = Conda(
            version=self.version_sphinx,
            build_env=self.build_env_mock,
        )
        python_env.install_requirements()
        self.build_env_mock.run.assert_not_called()
