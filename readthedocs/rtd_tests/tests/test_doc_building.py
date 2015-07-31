import os.path
import shutil
import uuid
import re

from django.test import TestCase
from django.contrib.auth.models import User
from mock import patch, Mock, PropertyMock

from readthedocs.projects.models import Project
from readthedocs.builds.models import Version
from readthedocs.doc_builder.environments import (DockerEnvironment,
                                                  DockerBuildCommand,
                                                  BuildCommand)
from readthedocs.rtd_tests.utils import make_test_git
from readthedocs.rtd_tests.base import RTDTestCase


class TestDockerEnvironment(TestCase):
    '''Test docker build environment'''

    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version)

    def test_container_id(self):
        '''Test docker build command'''
        docker = DockerEnvironment(version=self.version, project=self.project)
        self.assertEqual(docker.container_id,
                         'version-foobar-of-pip-20')


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

    @patch.object(DockerEnvironment, 'container_id', new_callable=PropertyMock)
    @patch.object(DockerEnvironment, 'get_client')
    def test_command_execution(self, mock_get_client, mock_container_id):
        '''Command execution through Docker'''
        docker_client = Mock(**{'foobar.return_value': 'foobar'})
        docker_client.exec_create.return_value = {'Id': 'container-foobar'}
        docker_client.exec_start.return_value = 'This is the return'
        docker_client.exec_inspect.return_value = {'ExitCode': 42}
        mock_get_client.return_value = docker_client
        mock_container_id.return_value = 'container-foobar'

        build_env = DockerEnvironment()
        cmd = DockerBuildCommand(['echo test'], build_env=build_env, cwd='/tmp')
        cmd.run()

        docker_client.exec_create.assert_called_with(
            container='container-foobar',
            cmd="/bin/sh -c 'cd /tmp && echo\\ test'",
            stderr=True,
            stdout=True
        )
        self.assertEqual(cmd.status, 42)
        self.assertEqual(cmd.output, 'This is the return')
        self.assertEqual(cmd.error, None)
