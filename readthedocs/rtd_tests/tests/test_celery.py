import os
from os.path import exists
import shutil
from tempfile import mkdtemp
from django.contrib.admin.models import User

from projects.models import Project
from projects import tasks

from rtd_tests.utils import make_test_git
from rtd_tests.tests.base import RTDTestCase


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
        assert exists(directory)
        result = tasks.remove_dir.delay(directory)
        assert result.successful()
        assert not exists(directory)
