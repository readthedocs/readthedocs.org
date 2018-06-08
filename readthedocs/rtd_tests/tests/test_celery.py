import os
import json
import shutil
from os.path import exists
from tempfile import mkdtemp

from django.contrib.auth.models import User
from django_dynamic_fixture import get
from mock import patch, MagicMock

from readthedocs.builds.constants import BUILD_STATE_INSTALLING, BUILD_STATE_FINISHED, LATEST
from readthedocs.builds.models import Build
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
        directory = self.project.get_production_media_path(type_='pdf', version_slug=version.slug)
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

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    def test_update_docs(self):
        build = get(Build, project=self.project,
                    version=self.project.versions.first())
        with mock_api(self.repo) as mapi:
            update_docs = tasks.UpdateDocsTask()
            result = update_docs.delay(
                self.project.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False)
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.update_build', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs')
    def test_update_docs_unexpected_setup_exception(self, mock_setup_vcs):
        exc = Exception()
        mock_setup_vcs.side_effect = exc
        build = get(Build, project=self.project,
                    version=self.project.versions.first())
        with mock_api(self.repo) as mapi:
            update_docs = tasks.UpdateDocsTask()
            result = update_docs.delay(
                self.project.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False)
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.update_build', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs')
    def test_update_docs_unexpected_build_exception(self, mock_build_docs):
        exc = Exception()
        mock_build_docs.side_effect = exc
        build = get(Build, project=self.project,
                    version=self.project.versions.first())
        with mock_api(self.repo) as mapi:
            update_docs = tasks.UpdateDocsTask()
            result = update_docs.delay(
                self.project.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False)
        self.assertTrue(result.successful())

    def test_sync_repository(self):
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            sync_repository = tasks.SyncRepositoryTask()
            result = sync_repository.apply_async(
                args=(version.pk,),
            )
        self.assertTrue(result.successful())

    def test_public_task_exception(self):
        """
        Test when a PublicTask rises an Exception.

        The exception should be catched and added to the ``info`` attribute of
        the result. Besides, the task should be SUCCESS.
        """
        from readthedocs.core.utils.tasks import PublicTask
        from readthedocs.worker import app

        class PublicTaskException(PublicTask):
            name = 'public_task_exception'

            def run_public(self):
                raise Exception('Something bad happened')

        app.tasks.register(PublicTaskException)
        exception_task = PublicTaskException()
        result = exception_task.delay()

        # although the task risen an exception, it's success since we add the
        # exception into the ``info`` attributes
        self.assertEqual(result.status, 'SUCCESS')
        self.assertEqual(result.info, {
            'task_name': 'public_task_exception',
            'context': {},
            'public_data': {},
            'error': 'Something bad happened',
        })
