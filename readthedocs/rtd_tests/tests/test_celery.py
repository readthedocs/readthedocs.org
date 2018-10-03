# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import os
import shutil
from os.path import exists
from tempfile import mkdtemp

from django.contrib.auth.models import User
from django_dynamic_fixture import get
from mock import patch, MagicMock

from readthedocs.builds.constants import LATEST
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.builds.models import Build
from readthedocs.projects.models import Project
from readthedocs.projects import tasks

from readthedocs.rtd_tests.utils import (
    create_git_branch, create_git_tag, delete_git_branch)
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
        result = tasks.clear_artifacts.delay(paths=version.get_artifact_paths())
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

        directory = version.project.rtd_build_path(version=version.slug)
        os.makedirs(directory)
        self.assertTrue(exists(directory))
        result = tasks.clear_artifacts.delay(paths=version.get_artifact_paths())
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    def test_update_docs(self):
        build = get(Build, project=self.project,
                    version=self.project.versions.first())
        with mock_api(self.repo) as mapi:
            result = tasks.update_docs_task.delay(
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
            result = tasks.update_docs_task.delay(
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
            result = tasks.update_docs_task.delay(
                self.project.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False)
        self.assertTrue(result.successful())

    def test_sync_repository(self):
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = tasks.sync_repository_task.delay(version.pk)
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.api_v2')
    def test_check_duplicate_reserved_version_latest(self, api_v2):
        create_git_branch(self.repo, 'latest')
        create_git_tag(self.repo, 'latest')

        version = self.project.versions.get(slug=LATEST)
        sync_repository = tasks.UpdateDocsTaskStep()
        sync_repository.version = version
        sync_repository.project = self.project
        with self.assertRaises(RepositoryError) as e:
            sync_repository.sync_repo()
        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS
        )

        delete_git_branch(self.repo, 'latest')
        sync_repository.sync_repo()
        api_v2.project().sync_versions.post.assert_called()

    @patch('readthedocs.projects.tasks.api_v2')
    def test_check_duplicate_reserved_version_stable(self, api_v2):
        create_git_branch(self.repo, 'stable')
        create_git_tag(self.repo, 'stable')

        version = self.project.versions.get(slug=LATEST)
        sync_repository = tasks.UpdateDocsTaskStep()
        sync_repository.version = version
        sync_repository.project = self.project
        with self.assertRaises(RepositoryError) as e:
            sync_repository.sync_repo()
        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS
        )

        # TODO: Check that we can build properly after
        # deleting the tag.

    @patch('readthedocs.projects.tasks.api_v2')
    def test_check_duplicate_no_reserved_version(self, api_v2):
        create_git_branch(self.repo, 'no-reserved')
        create_git_tag(self.repo, 'no-reserved')

        version = self.project.versions.get(slug=LATEST)
        sync_repository = tasks.UpdateDocsTaskStep()
        sync_repository.version = version
        sync_repository.project = self.project
        sync_repository.sync_repo()

        api_v2.project().sync_versions.post.assert_called()

    def test_public_task_exception(self):
        """
        Test when a PublicTask rises an Exception.

        The exception should be caught and added to the ``info`` attribute of
        the result. Besides, the task should be SUCCESS.
        """
        from readthedocs.core.utils.tasks import PublicTask
        from readthedocs.worker import app

        @app.task(name='public_task_exception', base=PublicTask)
        def public_task_exception():
            raise Exception('Something bad happened')

        result = public_task_exception.delay()

        # although the task risen an exception, it's success since we add the
        # exception into the ``info`` attributes
        self.assertEqual(result.status, 'SUCCESS')
        self.assertEqual(result.info, {
            'task_name': 'public_task_exception',
            'context': {},
            'public_data': {},
            'error': 'Something bad happened',
        })
