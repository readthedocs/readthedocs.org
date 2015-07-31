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


class TestLocalEnvironment(TestCase):
    '''Test execution and exception handling in environment'''
    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version)
        self.patches = {}
        self.mocks = {}
        self.patches['update_build'] = patch.object(LocalEnvironment,
                                                    'update_build')
        self.mocks['update_build'] = self.patches['update_build'].start()
        self.patches['Popen'] = patch('subprocess.Popen')
        self.mocks['Popen'] = self.patches['Popen'].start()

    def tearDown(self):
        for patch in self.patches:
            self.patches[patch].stop()

    def test_normal_execution(self):
        '''Normal build in passing state'''
        mock_popen = Mock()
        mock_popen.communicate.return_value = ('This is okay', None)
        type(mock_popen).returncode = PropertyMock(return_value=0)
        self.mocks['Popen'].return_value = mock_popen

        build_env = LocalEnvironment(version=self.version, project=self.project)
        with build_env:
            build_env.run('echo', 'test')
        self.assertTrue(mock_popen.communicate.called)
        self.assertTrue(build_env.successful)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, 'This is okay')

    def test_failing_execution(self):
        '''Build in failing state'''
        mock_popen = Mock()
        mock_popen.communicate.return_value = ('This is not okay', None)
        type(mock_popen).returncode = PropertyMock(return_value=1)
        self.mocks['Popen'].return_value = mock_popen

        build_env = LocalEnvironment(version=self.version, project=self.project)
        with build_env:
            build_env.run('echo', 'test')
            self.fail('This should be unreachable')
        self.assertTrue(mock_popen.communicate.called)
        self.assertTrue(build_env.failed)
        self.assertEqual(len(build_env.commands), 1)
        self.assertEqual(build_env.commands[0].output, 'This is not okay')

    def test_failing_execution_with_caught_exception(self):
        '''Build in failing state with BuildEnvironmentError exception'''
        mock_popen = Mock()
        mock_popen.communicate.return_value = ('This is okay', None)
        type(mock_popen).returncode = PropertyMock(return_value=0)
        self.mocks['Popen'].return_value = mock_popen

        build_env = LocalEnvironment(version=self.version, project=self.project)

        with build_env:
            raise BuildEnvironmentError('Foobar')
            build_env.run('echo', 'test')

        self.assertFalse(mock_popen.communicate.called)
        self.assertEqual(len(build_env.commands), 0)
        self.assertTrue(build_env.failed)

    def test_failing_execution_with_uncaught_exception(self):
        '''Build in failing state with exception from code'''
        mock_popen = Mock()
        mock_popen.communicate.return_value = ('This is okay', None)
        type(mock_popen).returncode = PropertyMock(return_value=0)
        self.mocks['Popen'].return_value = mock_popen

        build_env = LocalEnvironment(version=self.version, project=self.project)

        def _inner():
            with build_env:
                raise Exception()
                build_env.run('echo', 'test')

        self.assertRaises(Exception, _inner)
        self.assertFalse(mock_popen.communicate.called)
        self.assertTrue(build_env.failed)


class TestDockerEnvironment(TestCase):
    '''Test docker build environment'''

    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version)
        self.patches = {}
        self.mocks = {}
        self.patches['Client'] = patch(
            'readthedocs.doc_builder.environments.Client')
        self.mocks['Client'] = self.patches['Client'].start()
        self.patches['update_build'] = patch.object(DockerEnvironment,
                                                    'update_build')
        self.mocks['update_build'] = self.patches['update_build'].start()

    def tearDown(self):
        for patch in self.patches:
            self.patches[patch].stop()

    def test_container_id(self):
        '''Test docker build command'''
        docker = DockerEnvironment(version=self.version, project=self.project)
        self.assertEqual(docker.container_id,
                         'version-foobar-of-pip-20')

    def test_connection_failure(self):
        '''Connection failure on to docker socket should raise exception'''
        self.mocks['Client'].side_effect = DockerException
        build_env = DockerEnvironment(version=self.version, project=self.project)

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)

    def test_api_failure(self):
        '''Failing API error response from docker should raise exception'''
        response = Mock(status_code=500, reason='Because')
        client = Mock()
        client.create_container.side_effect = DockerAPIError(
            'Failure creating container', response, 'Failure creating container')
        self.mocks['Client'].return_value = client

        build_env = DockerEnvironment(version=self.version, project=self.project)

        def _inner():
            with build_env:
                self.fail('Should not hit this')

        self.assertRaises(BuildEnvironmentError, _inner)

    def test_command_execution(self):
        '''Command execution through Docker'''
        client = Mock()
        client.exec_create.return_value = {'Id': 'container-foobar'}
        client.exec_start.return_value = 'This is the return'
        client.exec_inspect.return_value = {'ExitCode': 42}
        self.mocks['Client'].return_value = client

        build_env = DockerEnvironment(version=self.version, project=self.project)
        with build_env:
            build_env.run('echo test', cwd='/tmp')

        client.exec_create.assert_called_with(
            container='version-foobar-of-pip-20',
            cmd="/bin/sh -c 'cd /tmp && echo\\ test'",
            stderr=True,
            stdout=True
        )
        self.assertEqual(build_env.commands[0].status, 42)
        self.assertEqual(build_env.commands[0].output, 'This is the return')
        self.assertEqual(build_env.commands[0].error, None)
        self.assertTrue(build_env.failed)

    def test_command_execution_cleanup_exception(self):
        '''Command execution through Docker, catch exception during cleanup'''
        response = Mock(status_code=500, reason='Because')
        client = Mock()
        client.exec_create.return_value = {'Id': 'container-foobar'}
        client.exec_start.return_value = 'This is the return'
        client.exec_inspect.return_value = {'ExitCode': 0}
        client.kill.side_effect = DockerAPIError(
            'Failure killing container', response, 'Failure killing container')
        self.mocks['Client'].return_value = client

        build_env = DockerEnvironment(version=self.version, project=self.project)
        with build_env:
            build_env.run('echo', 'test', cwd='/tmp')

        client.kill.assert_called_with('version-foobar-of-pip-20')
        self.assertTrue(build_env.successful)


class TestBuildCommand(TestCase):
    '''Test build command creation'''

    def test_command_env(self):
        '''Test build command env vars'''
        env = {'FOOBAR': 'foobar',
               'PATH': 'foobar'}
        cmd = BuildCommand('echo', environment=env)
        for key in env.keys():
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

    def test_exception_handling(self):
        # TODO
        pass

class TestDockerBuildCommand(TestCase):
    '''Test docker build commands'''

    def test_wrapped_command(self):
        '''Test shell wrapping for Docker chdir'''
        cmd = DockerBuildCommand(['pip', 'install', 'requests'],
                                 cwd='/tmp/foobar')
        self.assertEqual(
            cmd.get_wrapped_command(),
            ("/bin/sh -c "
             "'cd /tmp/foobar && "
             "pip install requests'"))
        cmd = DockerBuildCommand(['pip', 'install', 'Django>1.7'],
                                 cwd='/tmp/foobar')
        self.assertEqual(
            cmd.get_wrapped_command(),
            ("/bin/sh -c "
             "'cd /tmp/foobar && "
             "pip install Django\>1.7'"))
