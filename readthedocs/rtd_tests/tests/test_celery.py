from os.path import exists
import shutil
from tempfile import mkdtemp
from django.contrib.admin.models import User
import json

from projects.models import Project
from projects import tasks

from rtd_tests.utils import make_test_git
from rtd_tests.base import RTDTestCase
from rtd_tests.mocks.mock_api import MockApi


class TestCeleryBuilding(RTDTestCase):
    """These tests run the build functions directly. They don't use celery"""
    fixtures = ['eric.json']

    def setUp(self):
        repo = make_test_git()
        self.repo = repo
        super(TestCeleryBuilding, self).setUp()
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
        super(TestCeleryBuilding, self).tearDown()

    def test_remove_dir(self):
        directory = mkdtemp()
        self.assertTrue(exists(directory))
        result = tasks.remove_dir.delay(directory)
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    def test_update_docs(self):
        result = tasks.update_docs.delay(self.project.pk, record=False,
            intersphinx=False, api=MockApi(self.repo))
        self.assertTrue(result.successful())

    def test_update_imported_doc(self):
        result = tasks.update_imported_docs.delay(self.project.pk,
            api=MockApi(self.repo))
        self.assertTrue(result.successful())
