# -*- coding: utf-8 -*-
"""Things to know:

   * raw subprocess calls like .communicate expects bytes
   * the Command wrappers encapsulate the bytes and expose unicode
"""
from __future__ import absolute_import
from builtins import str
import os.path
import shutil
import uuid
import re

from django.test import TestCase
from django.contrib.auth.models import User
from mock import patch, Mock, PropertyMock
from docker.errors import APIError as DockerAPIError, DockerException

from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.doc_builder.environments import (DockerEnvironment,
                                                  DockerBuildCommand,
                                                  LocalEnvironment,
                                                  BuildCommand)
from readthedocs.doc_builder.exceptions import BuildEnvironmentError

from readthedocs.rtd_tests.utils import make_test_git
from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.rtd_tests.mocks.environment import EnvironmentMockGroup

DUMMY_BUILD_ID = 123
SAMPLE_UNICODE = u'HérÉ îß sömê ünïçó∂é'
SAMPLE_UTF8_BYTES = SAMPLE_UNICODE.encode('utf-8')

class TestLocalEnvironment(TestCase):
    '''Test execution and exception handling in environment'''
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
        '''Normal build in passing state'''
        self.mocks.configure_mock('process', {
            'communicate.return_value': (b'This is okay', '')})
        type(self.mocks.process).returncode = PropertyMock(return_value=0)

        build_env = LocalEnvironment(version=self.version, project=self.project,
                                     build={'id': DUMMY_BUILD_ID})
        with build_env:
            build_env.run('echo', 'test')
        self.assertTrue(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.successful)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, u'This is okay')
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_failing_execution(self):
        '''Build in failing state'''
        self.mocks.configure_mock('process', {
            'communicate.return_value': (b'This is not okay', '')})
        type(self.mocks.process).returncode = PropertyMock(return_value=1)

        build_env = LocalEnvironment(version=self.version, project=self.project,
                                     build={'id': DUMMY_BUILD_ID})
        with build_env:
            build_env.run('echo', 'test')
            self.fail('This should be unreachable')
        self.assertTrue(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, u'This is not okay')
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_failing_execution_with_caught_exception(self):
        '''Build in failing state with BuildEnvironmentError exception'''
        build_env = LocalEnvironment(version=self.version, project=self.project,
                                     build={'id': DUMMY_BUILD_ID})

        with build_env:
            raise BuildEnvironmentError('Foobar')

        self.assertFalse(self.mocks.process.communicate.called)
        self.assertEqual(len(build_env.commands), 0)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_failing_execution_with_unexpected_exception(self):
        '''Build in failing state with exception from code'''
        build_env = LocalEnvironment(version=self.version, project=self.project,
                                     build={'id': DUMMY_BUILD_ID})

        with build_env:
            raise ValueError('uncaught')

        self.assertFalse(self.mocks.process.communicate.called)
        self.assertTrue(build_env.done)
        self.assertTrue(build_env.failed)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)


class TestDockerEnvironment(TestCase):
    '''Test docker build environment'''

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
        '''Test docker build command'''
        docker = DockerEnvironment(version=self.version, project=self.project,
                                   build={'id': DUMMY_BUILD_ID})
        self.assertEqual(docker.container_id,
                         'build-123-project-6-pip')

    def test_connection_failure(self):
        '''Connection failure on to docker socket should raise exception'''
        self.mocks.configure_mock('docker', {
            'side_effect': DockerException
        })
        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_api_failure(self):
        '''Failing API error response from docker should raise exception'''
        response = Mock(status_code=500, reason='Because')
        self.mocks.configure_mock('docker_client', {
            'create_container.side_effect': DockerAPIError(
                'Failure creating container',
                response,
                'Failure creating container'
            )
        })

        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_command_execution(self):
        '''Command execution through Docker'''
        self.mocks.configure_mock('docker_client', {
            'exec_create.return_value': {'Id': b'container-foobar'},
            'exec_start.return_value': b'This is the return',
            'exec_inspect.return_value': {'ExitCode': 1},
        })

        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})
        with build_env:
            build_env.run('echo test', cwd='/tmp')

        self.mocks.docker_client.exec_create.assert_called_with(
            container='build-123-project-6-pip',
            cmd="/bin/sh -c 'cd /tmp && echo\\ test'",
            stderr=True,
            stdout=True
        )
        self.assertEqual(build_env.commands[0].exit_code, 1)
        self.assertEqual(build_env.commands[0].output, u'This is the return')
        self.assertEqual(build_env.commands[0].error, None)
        self.assertTrue(build_env.failed)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_command_execution_cleanup_exception(self):
        '''Command execution through Docker, catch exception during cleanup'''
        response = Mock(status_code=500, reason='Because')
        self.mocks.configure_mock('docker_client', {
            'exec_create.return_value': {'Id': b'container-foobar'},
            'exec_start.return_value': b'This is the return',
            'exec_inspect.return_value': {'ExitCode': 0},
            'kill.side_effect': DockerAPIError(
                'Failure killing container',
                response,
                'Failure killing container'
            )
        })

        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        self.mocks.docker_client.kill.assert_called_with(
            'build-123-project-6-pip')
        self.assertTrue(build_env.successful)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_container_already_exists(self):
        '''Docker container already exists'''
        self.mocks.configure_mock('docker_client', {
            'inspect_container.return_value': {'State': {'Running': True}},
            'exec_create.return_value': {'Id': b'container-foobar'},
            'exec_start.return_value': b'This is the return',
            'exec_inspect.return_value': {'ExitCode': 0},
        })

        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})
        def _inner():
            with build_env:
                build_env.run('echo', 'test', cwd='/tmp')

        self.assertRaises(BuildEnvironmentError, _inner)
        self.assertEqual(
            str(build_env.failure),
            'A build environment is currently running for this version')
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 0)
        self.assertTrue(build_env.failed)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)

    def test_container_timeout(self):
        '''Docker container timeout and command failure'''
        response = Mock(status_code=404, reason='Container not found')
        self.mocks.configure_mock('docker_client', {
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

        build_env = DockerEnvironment(version=self.version, project=self.project,
                                      build={'id': DUMMY_BUILD_ID})
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        self.assertEqual(
            str(build_env.failure),
            'Build exited due to time out')
        self.assertEqual(self.mocks.docker_client.exec_create.call_count, 1)
        self.assertTrue(build_env.failed)
        self.assertFalse(self.mocks.api()(DUMMY_BUILD_ID).put.called)


class TestBuildCommand(TestCase):
    '''Test build command creation'''

    def test_command_env(self):
        '''Test build command env vars'''
        env = {'FOOBAR': 'foobar',
               'BIN_PATH': 'foobar'}
        cmd = BuildCommand('echo', environment=env)
        for key in list(env.keys()):
            self.assertEqual(cmd.environment[key], env[key])

    def test_result(self):
        '''Test result of output using unix true/false commands'''
        cmd = BuildCommand('true')
        cmd.run()
        self.assertTrue(cmd.successful)

        cmd = BuildCommand('false')
        cmd.run()
        self.assertTrue(cmd.failed)

    def test_missing_command(self):
        '''Test missing command'''
        path = os.path.join('non-existant', str(uuid.uuid4()))
        self.assertFalse(os.path.exists(path))
        cmd = BuildCommand(path)
        cmd.run()
        missing_re = re.compile(r'(?:No such file or directory|not found)')
        self.assertRegexpMatches(cmd.error, missing_re)

    def test_input(self):
        '''Test input to command'''
        cmd = BuildCommand('/bin/cat', input_data='FOOBAR')
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')

    def test_output(self):
        '''Test output command'''
        cmd = BuildCommand(['/bin/bash',
                            '-c', 'echo -n FOOBAR'])
        cmd.run()
        self.assertEqual(cmd.output, "FOOBAR")

    def test_error_output(self):
        '''Test error output from command'''
        # Test default combined output/error streams
        cmd = BuildCommand(['/bin/bash',
                            '-c', 'echo -n FOOBAR 1>&2'])
        cmd.run()
        self.assertEqual(cmd.output, 'FOOBAR')
        self.assertIsNone(cmd.error)
        # Test non-combined streams
        cmd = BuildCommand(['/bin/bash',
                            '-c', 'echo -n FOOBAR 1>&2'],
                           combine_output=False)
        cmd.run()
        self.assertEqual(cmd.output, '')
        self.assertEqual(cmd.error, 'FOOBAR')

    @patch('subprocess.Popen')
    def test_unicode_output(self, mock_subprocess):
        '''Unicode output from command'''
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
    '''Test docker build commands'''

    def setUp(self):
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    def test_wrapped_command(self):
        '''Test shell wrapping for Docker chdir'''
        cmd = DockerBuildCommand(['pip', 'install', 'requests'],
                                 cwd='/tmp/foobar')
        self.assertEqual(
            cmd.get_wrapped_command(),
            ("/bin/sh -c "
             "'cd /tmp/foobar && "
             "pip install requests'"))
        cmd = DockerBuildCommand(['python', '/tmp/foo/pip', 'install',
                                  'Django>1.7'],
                                 cwd='/tmp/foobar',
                                 bin_path='/tmp/foo')
        self.assertEqual(
            cmd.get_wrapped_command(),
            ("/bin/sh -c "
             "'cd /tmp/foobar && PATH=/tmp/foo:$PATH "
             "python /tmp/foo/pip install Django\>1.7'"))

    def test_unicode_output(self):
        '''Unicode output from command'''
        self.mocks.configure_mock('docker_client', {
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
        '''Command is OOM killed'''
        self.mocks.configure_mock('docker_client', {
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
