# -*- coding: utf-8 -*-
"""
Things to know:

* raw subprocess calls like .communicate expects bytes
* the Command wrappers encapsulate the bytes and expose unicode
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import os.path
import re
import uuid
from builtins import str

import mock
import pytest
from django.test import TestCase
from docker.errors import APIError as DockerAPIError
from docker.errors import DockerException
from mock import Mock, PropertyMock, mock_open, patch

from readthedocs.builds.constants import BUILD_STATE_CLONING
from readthedocs.builds.models import Version
from readthedocs.doc_builder.config import ConfigWrapper
from readthedocs.doc_builder.environments import (
    BuildCommand, DockerBuildCommand, DockerBuildEnvironment, LocalBuildEnvironment)
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.mocks.environment import EnvironmentMockGroup
from readthedocs.rtd_tests.tests.test_config_wrapper import create_load

DUMMY_BUILD_ID = 123
SAMPLE_UNICODE = u'HérÉ îß sömê ünïçó∂é'
SAMPLE_UTF8_BYTES = SAMPLE_UNICODE.encode('utf-8')


class TestLocalBuildEnvironment(TestCase):

    """Test execution and exception handling in environment."""
    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version, bulk=False)
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    def test_normal_execution(self):
        """Normal build in passing state."""
        self.mocks.configure_mock('process', {
            'communicate.return_value': (b'This is okay', '')
        })
        type(self.mocks.process).returncode = PropertyMock(return_value=0)

        build_env = LocalBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            build_env.run('echo', 'test')
        self.assertTrue(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.successful)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, u'This is okay')

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': True,
            'project': self.project.pk,
            'setup_error': u'',
            'length': mock.ANY,
            'error': '',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
            'exit_code': 0,
        })

    def test_incremental_state_update_with_no_update(self):
        """Build updates to a non-finished state when update_on_success=True."""
        build_envs = [
            LocalBuildEnvironment(
                version=self.version,
                project=self.project,
                build={'id': DUMMY_BUILD_ID},
            ),
            LocalBuildEnvironment(
                version=self.version,
                project=self.project,
                build={'id': DUMMY_BUILD_ID},
                update_on_success=False,
            ),
        ]

        for build_env in build_envs:
            with build_env:
                build_env.update_build(BUILD_STATE_CLONING)
                self.mocks.mocks['api_v2.build']().put.assert_called_with({
                    'id': DUMMY_BUILD_ID,
                    'version': self.version.pk,
                    'success': True,
                    'project': self.project.pk,
                    'setup_error': u'',
                    'length': mock.ANY,
                    'error': '',
                    'setup': u'',
                    'output': u'',
                    'state': BUILD_STATE_CLONING,
                    'builder': mock.ANY,
                    'exit_code': 0,
                })

    def test_failing_execution(self):
        """Build in failing state."""
        self.mocks.configure_mock('process', {
            'communicate.return_value': (b'This is not okay', '')
        })
        type(self.mocks.process).returncode = PropertyMock(return_value=1)

        build_env = LocalBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            build_env.run('echo', 'test')
            self.fail('This should be unreachable')
        self.assertTrue(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, u'This is not okay')

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'length': mock.ANY,
            'error': '',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
            'exit_code': 1,
        })

    def test_failing_execution_with_caught_exception(self):
        """Build in failing state with BuildEnvironmentError exception."""
        build_env = LocalBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            raise BuildEnvironmentError('Foobar')

        self.assertFalse(self.mocks.process.communicate.called)
        self.assertEqual(len(build_env.commands), 0)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'length': mock.ANY,
            'error': 'Foobar',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
            'exit_code': 1,
        })

    def test_failing_execution_with_unexpected_exception(self):
        """Build in failing state with exception from code."""
        build_env = LocalBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            raise ValueError('uncaught')

        self.assertFalse(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'length': mock.ANY,
            'error': (
                'There was a problem with Read the Docs while building your '
                'documentation. Please report this to us with your build id (123).'
            ),
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })


class TestDockerBuildEnvironment(TestCase):

    """Test docker build environment."""

    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version, bulk=False)
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    def test_container_id(self):
        """Test docker build command."""
        docker = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )
        self.assertEqual(docker.container_id, 'build-123-project-6-pip')

    def test_environment_successful_build(self):
        """A successful build exits cleanly and reports the build output."""
        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            pass

        self.assertTrue(build_env.successful)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': True,
            'project': self.project.pk,
            'setup_error': u'',
            'length': 0,
            'error': '',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_environment_successful_build_without_update(self):
        """A successful build exits cleanly and doesn't update build."""
        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
            update_on_success=False,
        )

        with build_env:
            pass

        self.assertTrue(build_env.successful)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.assertFalse(self.mocks.mocks['api_v2.build']().put.called)

    def test_environment_failed_build_without_update_but_with_error(self):
        """A failed build exits cleanly and doesn't update build."""
        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
            update_on_success=False,
        )

        with build_env:
            raise BuildEnvironmentError('Test')

        self.assertFalse(build_env.successful)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': 'Test',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_connection_failure(self):
        """Connection failure on to docker socket should raise exception."""
        self.mocks.configure_mock('docker', {'side_effect': DockerException})
        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': (
                "There was a problem with Read the Docs while building your "
                "documentation. Please report this to us with your build id "
                "(123)."
            ),
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_api_failure(self):
        """Failing API error response from docker should raise exception."""
        response = Mock(status_code=500, reason='Because')
        self.mocks.configure_mock(
            'docker_client', {
                'create_container.side_effect': DockerAPIError(
                    'Failure creating container', response,
                    'Failure creating container')
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': mock.ANY,
            'error': 'Build environment creation failed',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_api_failure_on_docker_memory_limit(self):
        """Docker exec_create raised memory issue on `exec`"""
        response = Mock(status_code=500, reason='Internal Server Error')
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.side_effect': DockerAPIError(
                    'Failure creating container', response,
                    'Failure creating container'),
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            build_env.run('echo test', cwd='/tmp')

        self.assertEqual(build_env.commands[0].exit_code, -1)
        self.assertEqual(build_env.commands[0].error, None)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': -1,
            'length': mock.ANY,
            'error': '',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_api_failure_on_error_in_exit(self):
        response = Mock(status_code=500, reason='Internal Server Error')
        self.mocks.configure_mock('docker_client', {
            'kill.side_effect': BuildEnvironmentError('Failed')
        })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            pass

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': 'Failed',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_api_failure_returns_previous_error_on_error_in_exit(self):
        """
        Treat previously raised errors with more priority.

        Don't report a connection problem to Docker on cleanup if we have a more
        usable error to show the user.
        """
        response = Mock(status_code=500, reason='Internal Server Error')
        self.mocks.configure_mock('docker_client', {
            'kill.side_effect': BuildEnvironmentError('Outer failed')
        })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            raise BuildEnvironmentError('Inner failed')

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': 'Inner failed',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_command_execution(self):
        """Command execution through Docker."""
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'This is the return',
                'exec_inspect.return_value': {'ExitCode': 1},
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        with build_env:
            build_env.run('echo test', cwd='/tmp')

        self.mocks.docker_client.exec_create.assert_called_with(
            container='build-123-project-6-pip',
            cmd="/bin/sh -c 'cd /tmp && echo\\ test'", stderr=True, stdout=True)
        self.assertEqual(build_env.commands[0].exit_code, 1)
        self.assertEqual(build_env.commands[0].output, u'This is the return')
        self.assertEqual(build_env.commands[0].error, None)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': '',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_command_execution_cleanup_exception(self):
        """Command execution through Docker, catch exception during cleanup."""
        response = Mock(status_code=500, reason='Because')
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'This is the return',
                'exec_inspect.return_value': {'ExitCode': 0},
                'kill.side_effect': DockerAPIError(
                    'Failure killing container',
                    response,
                    'Failure killing container',
                )
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        self.mocks.docker_client.kill.assert_called_with(
            'build-123-project-6-pip')
        self.assertTrue(build_env.successful)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'error': '',
            'success': True,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 0,
            'length': 0,
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })

    def test_container_already_exists(self):
        """Docker container already exists."""
        self.mocks.configure_mock(
            'docker_client', {
                'inspect_container.return_value': {'State': {'Running': True}},
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': b'This is the return',
                'exec_inspect.return_value': {'ExitCode': 0},
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )

        def _inner():
            with build_env:
                build_env.run('echo', 'test', cwd='/tmp')

        self.assertRaises(BuildEnvironmentError, _inner)
        self.assertEqual(
            str(build_env.failure),
            'A build environment is currently running for this version')
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 0)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': 'A build environment is currently running for this version',
            'setup': u'',
            'output': u'',
            'state': u'finished',
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
            })

        build_env = DockerBuildEnvironment(
            version=self.version,
            project=self.project,
            build={'id': DUMMY_BUILD_ID},
        )
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        self.assertEqual(str(build_env.failure), 'Build exited due to time out')
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)
        self.assertTrue(build_env.failed)

        # api() is not called anymore, we use api_v2 instead
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)
        self.mocks.mocks['api_v2.build']().put.assert_called_with({
            'id': DUMMY_BUILD_ID,
            'version': self.version.pk,
            'success': False,
            'project': self.project.pk,
            'setup_error': u'',
            'exit_code': 1,
            'length': 0,
            'error': 'Build exited due to time out',
            'setup': u'',
            'output': u'',
            'state': u'finished',
            'builder': mock.ANY,
        })


class TestBuildCommand(TestCase):

    """Test build command creation."""

    def test_command_env(self):
        """Test build command env vars."""
        env = {'FOOBAR': 'foobar', 'BIN_PATH': 'foobar'}
        cmd = BuildCommand('echo', environment=env)
        for key in list(env.keys()):
            self.assertEqual(cmd.environment[key], env[key])

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
        missing_re = re.compile(r'(?:No such file or directory|not found)')
        self.assertRegexpMatches(cmd.error, missing_re)

    def test_input(self):
        """Test input to command."""
        cmd = BuildCommand('/bin/cat', input_data='FOOBAR')
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')

    def test_output(self):
        """Test output command."""
        cmd = BuildCommand(['/bin/bash', '-c', 'echo -n FOOBAR'])
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')

    def test_error_output(self):
        """Test error output from command."""
        # Test default combined output/error streams
        cmd = BuildCommand(['/bin/bash', '-c', 'echo -n FOOBAR 1>&2'])
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')
        self.assertIsNone(cmd.error)
        # Test non-combined streams
        cmd = BuildCommand(['/bin/bash', '-c', 'echo -n FOOBAR 1>&2'],
                           combine_output=False)
        cmd.run()
        self.assertEqual(cmd.output, '')
        self.assertEqual(cmd.error, 'FOOBAR')

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
            u'H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9')


class TestDockerBuildCommand(TestCase):

    """Test docker build commands."""

    def setUp(self):
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    def test_wrapped_command(self):
        """Test shell wrapping for Docker chdir."""
        cmd = DockerBuildCommand(['pip', 'install', 'requests'],
                                 cwd='/tmp/foobar')
        self.assertEqual(
            cmd.get_wrapped_command(),
            "/bin/sh -c 'cd /tmp/foobar && pip install requests'",
        )
        cmd = DockerBuildCommand(
            ['python', '/tmp/foo/pip', 'install', 'Django>1.7'],
            cwd='/tmp/foobar',
            bin_path='/tmp/foo',
        )
        self.assertEqual(
            cmd.get_wrapped_command(),
            ('/bin/sh -c '
             "'cd /tmp/foobar && PATH=/tmp/foo:$PATH "
             "python /tmp/foo/pip install Django\>1.7'"),
        )

    def test_unicode_output(self):
        """Unicode output from command."""
        self.mocks.configure_mock(
            'docker_client', {
                'exec_create.return_value': {'Id': b'container-foobar'},
                'exec_start.return_value': SAMPLE_UTF8_BYTES,
                'exec_inspect.return_value': {'ExitCode': 0},
            })
        cmd = DockerBuildCommand(['echo', 'test'], cwd='/tmp/foobar')
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value='foo')
        cmd.run()
        self.assertEqual(
            cmd.output,
            u'H\xe9r\xc9 \xee\xdf s\xf6m\xea \xfcn\xef\xe7\xf3\u2202\xe9')
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
            })
        cmd = DockerBuildCommand(['echo', 'test'], cwd='/tmp/foobar')
        cmd.build_env = Mock()
        cmd.build_env.get_client.return_value = self.mocks.docker_client
        type(cmd.build_env).container_id = PropertyMock(return_value='foo')
        cmd.run()
        self.assertEqual(
            str(cmd.output),
            u'Command killed due to excessive memory consumption\n')




class TestAutoWipeEnvironment(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.pip = Project.objects.get(slug='pip')
        self.version = self.pip.versions.get(slug='0.8')

    def test_is_obsolete_without_env_json_file(self):
        yaml_config = create_load()()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        with patch('os.path.exists') as exists:
            exists.return_value = False
            python_env = Virtualenv(
                version=self.version,
                build_env=None,
                config=config,
            )

        self.assertFalse(python_env.is_obsolete)

    def test_is_obsolete_with_invalid_env_json_file(self):
        yaml_config = create_load()()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        with patch('os.path.exists') as exists:
            exists.return_value = True
            python_env = Virtualenv(
                version=self.version,
                build_env=None,
                config=config,
            )

        self.assertFalse(python_env.is_obsolete)

    def test_is_obsolete_with_json_different_python_version(self):
        config_data = {
            'build': {
                'image': '2.0',
            },
            'python': {
                'version': 2.7,
            },
        }
        yaml_config = create_load(config_data)()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        python_env = Virtualenv(
            version=self.version,
            build_env=None,
            config=config,
        )
        env_json_data = '{"build": {"image": "readthedocs/build:2.0"}, "python": {"version": 3.5}}'
        with patch('os.path.exists') as exists, patch('readthedocs.doc_builder.python_environments.open', mock_open(read_data=env_json_data)) as _open:  # noqa
            exists.return_value = True
            self.assertTrue(python_env.is_obsolete)

    @pytest.mark.xfail(reason='build.image is not being considered yet')
    def test_is_obsolete_with_json_different_build_image(self):
        config_data = {
            'build': {
                'image': 'latest',
            },
            'python': {
                'version': 2.7,
            },
        }
        yaml_config = create_load(config_data)()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        python_env = Virtualenv(
            version=self.version,
            build_env=None,
            config=config,
        )
        env_json_data = '{"build": {"image": "readthedocs/build:2.0"}, "python": {"version": 2.7}}'
        with patch('os.path.exists') as exists, patch('readthedocs.doc_builder.python_environments.open', mock_open(read_data=env_json_data)) as _open:  # noqa
            exists.return_value = True
            self.assertTrue(python_env.is_obsolete)

    def test_is_obsolete_with_project_different_build_image(self):
        config_data = {
            'build': {
                'image': '2.0',
            },
            'python': {
                'version': 2.7,
            },
        }
        yaml_config = create_load(config_data)()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        # Set container_image manually
        self.pip.container_image = 'readthedocs/build:latest'
        self.pip.save()

        python_env = Virtualenv(
            version=self.version,
            build_env=None,
            config=config,
        )
        env_json_data = '{"build": {"image": "readthedocs/build:2.0"}, "python": {"version": 2.7}}'
        with patch('os.path.exists') as exists, patch('readthedocs.doc_builder.python_environments.open', mock_open(read_data=env_json_data)) as _open:  # noqa
            exists.return_value = True
            self.assertTrue(python_env.is_obsolete)

    def test_is_obsolete_with_json_same_data_as_version(self):
        config_data = {
            'build': {
                'image': '2.0',
            },
            'python': {
                'version': 3.5,
            },
        }
        yaml_config = create_load(config_data)()[0]
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)

        python_env = Virtualenv(
            version=self.version,
            build_env=None,
            config=config,
        )
        env_json_data = '{"build": {"image": "readthedocs/build:2.0"}, "python": {"version": 3.5}}'
        with patch('os.path.exists') as exists, patch('readthedocs.doc_builder.python_environments.open', mock_open(read_data=env_json_data)) as _open:  # noqa
            exists.return_value = True
            self.assertFalse(python_env.is_obsolete)
