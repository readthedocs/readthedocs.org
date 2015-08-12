import os
import json
import shutil
from os.path import exists
from tempfile import mkdtemp

from django.contrib.auth.models import User
from mock import patch, MagicMock

from readthedocs.projects.models import Project
from readthedocs.projects import tasks

from readthedocs.rtd_tests.utils import make_test_git
from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.rtd_tests.mocks.mock_api import mock_api


class TestCeleryBuilding(RTDTestCase):

    """These tests run the build functions directly. They don't use celery"""

    def setUp(self):
        repo = make_test_git()
        self.repo = repo
        super(TestCeleryBuilding, self).setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name="Test Project",
            repo_type="git",
            # Our top-level checkout
            repo=repo,
        )
        self.project.users.add(self.eric)

    def tearDown(self):
        shutil.rmtree(self.repo)
        super(TestCeleryBuilding, self).tearDown()

    def test_remove_dir(self):
        directory = mkdtemp()
        self.assertTrue(exists(directory))
        result = tasks.remove_dir.delay(directory)
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    def test_clear_artifacts(self):
        version = self.project.versions.all()[0]
        directory = self.project.get_production_media_path(type='pdf', version_slug=version.slug)
        os.makedirs(directory)
        self.assertTrue(exists(directory))
        result = tasks.clear_artifacts.delay(version_pk=version.pk)
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

        directory = version.project.rtd_build_path(version=version.slug)
        os.makedirs(directory)
        self.assertTrue(exists(directory))
        result = tasks.clear_artifacts.delay(version_pk=version.pk)
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    @patch('readthedocs.projects.tasks.UpdateDocsTask.build_docs',
           new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTask.setup_vcs',
           new=MagicMock)
    def test_update_docs(self):
        with mock_api(self.repo):
            update_docs = tasks.UpdateDocsTask()
            result = update_docs.delay(self.project.pk, record=False,
                                       intersphinx=False)
        self.assertTrue(result.successful())

    def test_update_imported_doc(self):
        with mock_api(self.repo):
            result = tasks.update_imported_docs.delay(self.project.pk)
        self.assertTrue(result.successful())
