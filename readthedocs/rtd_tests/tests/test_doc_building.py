import base64
import json
import os
from os.path import join as pjoin
import shutil
from subprocess import check_output
from tempfile import gettempdir, mkdtemp

from django.conf import settings
from django.contrib.admin.models import User

from projects.models import Project
from projects import tasks

from .base import RTDTestCase

class TestBuilding(RTDTestCase):
    fixtures = ['eric.json']

    def make_test_git(self):
        directory = mkdtemp()
        path = os.getcwd()
        sample = os.path.abspath(pjoin(path, 'rtd_tests/fixtures/sample_git'))
        directory = pjoin(directory, 'sample_git')
        shutil.copytree(sample, directory)
        env = os.environ.copy()
        env['GIT_DIR'] = pjoin(directory, '.git')
        os.chdir(directory)
        print check_output(['git', 'init'] + [directory], env=env)
        print check_output(['git', 'add', '.'], env=env)
        print check_output(['git', 'ci', '-m"init"'], env=env)
        return directory

    def setUp(self):
        repo = self.make_test_git()
        super(TestBuilding, self).setUp()
        self.eric = User.objects.get(username='eric')
        self.project = Project.objects.create(
            user = self.eric,
            name="Test Project",
            repo_type="git",
            #Our top-level checkout
            repo=repo
        )

    def tearDown(self):
        directory = gettempdir()
        shutil.rmtree(directory)
        super(TestBuilding, self).tearDown()

    def test_default_project_build(self):
        """
        Test that a superuser can use the API
        """
        tasks.update_docs(pk=self.project.pk)
        self.assertTrue(os.path.exists(
            os.path.join(self.project.rtd_build_path(), 'index.html')
        ))

    '''
    def test_version_project_build(self):
        """
        Test that a superuser can use the API
        """
        tasks.update_docs(pk=self.project.pk, version_pk=self.version.pk)
        self.assertTrue(os.path.exists(
            os.path.join(self.project.rtd_build_path(), 'index.html')
        ))
    '''
