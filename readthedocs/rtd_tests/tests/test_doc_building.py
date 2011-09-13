import os
import shutil

from django.contrib.admin.models import User

from projects.models import Project
from projects import tasks

from rtd_tests.utils import make_test_git
from rtd_tests.tests.base import RTDTestCase


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

    def test_default_project_build(self):
        """
        Test that a superuser can use the API
        """
        tasks.update_docs(pk=self.project.pk)
        self.assertTrue(os.path.exists(
            os.path.join(self.project.rtd_build_path(), 'index.html')
        ))

    # def test_version_project_build(self):
    #     """
    #     Test that a superuser can use the API
    #     """
    #     tasks.update_docs(pk=self.project.pk, version_pk=self.version.pk)
    #     self.assertTrue(os.path.exists(
    #         os.path.join(self.project.rtd_build_path(), 'index.html')
    #     ))
