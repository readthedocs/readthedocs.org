import os.path
import shutil
import uuid

from django.test import TestCase
from django.contrib.auth.models import User

from projects.models import Project
from builds.models import Version
from doc_builder.environments import (DockerEnvironment, DockerBuildCommand,
                                      BuildCommand)
from rtd_tests.utils import make_test_git
from rtd_tests.base import RTDTestCase


class TestBuilding(RTDTestCase):
    """These tests run the build functions directly. They don't use celery"""
    fixtures = ['eric.json']

    def setUp(self):
        repo = make_test_git()
        self.repo = repo
        super(TestBuilding, self).setUp()
        self.eric = User.objects.get(username='eric')
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="git",
            #Our top-level checkout
            repo=repo,
        )
        self.project.users.add(self.eric)

    def tearDown(self):
        shutil.rmtree(self.repo)
        super(TestBuilding, self).tearDown()


class TestDockerEnvironment(TestCase):
    '''Test docker build environment'''

    fixtures = ['test_data']

    def setUp(self):
        self.project = Project.objects.get(slug='pip')
        self.version = Version(slug='foo', verbose_name='foobar')
        self.project.versions.add(self.version)

    def test_container_id(self):
        '''Test docker build command'''
        docker = DockerEnvironment(self.version)
        self.assertEqual(docker.container_id(),
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
        with cmd:
            cmd.run()
        self.assertTrue(cmd.successful())

        cmd = BuildCommand('false')
        with cmd:
            cmd.run()
        self.assertTrue(cmd.failed())

    def test_missing_command(self):
        '''Test missing command'''
        path = os.path.join('non-existant', str(uuid.uuid4()))
        self.assertFalse(os.path.exists(path))
        cmd = BuildCommand('/non-existant/foobar')
        with cmd:
            cmd.run()
        self.assertIn('No such file or directory', cmd.error)

    def test_input(self):
        '''Test input to command'''
        cmd = BuildCommand('/bin/cat')
        with cmd:
            cmd.run(cmd_input="FOOBAR")
        self.assertEqual(cmd.output, "FOOBAR")

    def test_output(self):
        '''Test output command'''
        cmd = BuildCommand('/bin/bash -c "echo -n FOOBAR"')
        with cmd:
            cmd.run()
        self.assertEqual(cmd.output, "FOOBAR")

    def test_error_output(self):
        '''Test error output from command'''
        cmd = BuildCommand('/bin/bash -c "echo -n FOOBAR 1>&2"')
        with cmd:
            cmd.run()
        self.assertEqual(cmd.output, "")
        self.assertEqual(cmd.error, "FOOBAR")


class TestDockerBuildCommand(TestCase):
    '''Test docker build commands'''

    def test_command_build(self):
        '''Test building of command'''
        cmd = DockerBuildCommand('/home/docs/run.sh pip')
        with cmd:
            self.assertEqual(
                cmd.get_command(),
                'docker run -i --rm=true rtfd-build /home/docs/run.sh pip')

        cmd = DockerBuildCommand(['/home/docs/run.sh', 'pip'])
        with cmd:
            self.assertEqual(
                cmd.get_command(),
                'docker run -i --rm=true rtfd-build /home/docs/run.sh pip')

        cmd = DockerBuildCommand(
            ['/home/docs/run.sh', 'pip'],
            name='swayze-express',
            mounts=[('/some/path/checkouts',
                     '/home/docs/checkouts')]
        )
        with cmd:
            self.assertEqual(
                cmd.get_command(),
                ('docker run -i -v /some/path/checkouts:/home/docs/checkouts '
                 '--name=swayze-express --rm=true rtfd-build '
                 '/home/docs/run.sh pip')
            )

        cmd = DockerBuildCommand(
            ['/home/docs/run.sh', 'pip'],
            user='pswayze',
            image='swayze-express',
        )
        with cmd:
            self.assertEqual(
                cmd.get_command(),
                ('docker run -i --user=pswayze --rm=true swayze-express '
                 '/home/docs/run.sh pip')
            )

        cmd = DockerBuildCommand(
            ['/home/docs/run.sh', 'pip'],
            user='pswayze',
            image='swayze-express',
            remove=False,
        )
        with cmd:
            self.assertEqual(
                cmd.get_command(),
                ('docker run -i --user=pswayze swayze-express '
                 '/home/docs/run.sh pip')
            )

    def test_command_exception(self):
        '''Test exception in context manager'''
        cmd = DockerBuildCommand('echo test')

        def _inner():
            with cmd:
                raise Exception('FOOBAR EXCEPTION')

        self.assertRaises(Exception, _inner)
        self.assertIn('FOOBAR EXCEPTION', cmd.error)
