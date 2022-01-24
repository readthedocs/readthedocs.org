import os
import shutil
from os.path import exists
from tempfile import mkdtemp
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get
from messages_extends.models import Message

from readthedocs.builds import tasks as build_tasks
from readthedocs.builds.constants import (
    BUILD_STATE_TRIGGERED,
    BUILD_STATUS_SUCCESS,
    EXTERNAL,
    LATEST,
)
from readthedocs.builds.models import Build, Version
from readthedocs.config.config import BuildConfigV2
from readthedocs.doc_builder.environments import (
    BuildEnvironment,
    LocalBuildEnvironment,
)
from readthedocs.doc_builder.exceptions import VersionLockedError
from readthedocs.oauth.models import RemoteRepository, RemoteRepositoryRelation
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Project
from readthedocs.projects.tasks.builds import sync_repository_task, update_docs_task
from readthedocs.projects.tasks.search import fileify
from readthedocs.rtd_tests.mocks.mock_api import mock_api
from readthedocs.rtd_tests.utils import (
    create_git_branch,
    create_git_tag,
    delete_git_branch,
    make_test_git,
)


# NOTE: most of these tests need to be re-written making usage of the new
# Celery handlers. These are exactly the tests we are interested in making them
# work properly (e.g. send notifications after build, handle unexpected
# exceptions, etc)
@pytest.mark.skip
class TestCeleryBuilding(TestCase):

    """
    These tests run the build functions directly.

    They don't use celery
    """

    def setUp(self):
        repo = make_test_git()
        self.repo = repo
        super().setUp()
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()
        self.project = Project.objects.create(
            name='Test Project',
            repo_type='git',
            # Our top-level checkout
            repo=repo,
        )
        self.project.users.add(self.eric)
        self.version = self.project.versions.get(slug=LATEST)

    def tearDown(self):
        shutil.rmtree(self.repo)
        super().tearDown()

    @patch('readthedocs.projects.tasks.utils.clean_build')
    def test_clean_build_after_sync_repository(self, clean_build):
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = sync_repository_task.delay(version.pk)
        self.assertTrue(result.successful())
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.SyncRepositoryTaskStep.run')
    @patch('readthedocs.projects.tasks.utils.clean_build')
    def test_clean_build_after_failure_in_sync_repository(self, clean_build, run_syn_repository):
        run_syn_repository.side_effect = Exception()
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = sync_repository_task.delay(version.pk)
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_check_duplicate_reserved_version_latest(self, checkout_path):
        # NOTE: these kind of tests should be split into unit-test that test
        # the `SyncRepositoryMixin.validate_duplicate_reserved_versions` login
        # and another integration test that checks that function is called by
        # `sync_repository_task`. Otherwise, we need a lot of overhead
        # requiring "build environment" and executing real git commands on
        # tests :/
        create_git_branch(self.repo, 'latest')
        create_git_tag(self.repo, 'latest')

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        version = self.project.versions.get(slug=LATEST)
        with self.assertRaises(RepositoryError) as e:
            sync_repository = sync_repository_task(version_id=version.pk)

        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        )

        delete_git_branch(self.repo, 'latest')

        sync_repository_task(version_id=version.pk)
        self.assertTrue(self.project.versions.filter(slug=LATEST).exists())

    # NOTE: tasks must not be trigger by calling them directly but using
    # `.delay`/`.async` because otherwise the Celery handlers are not executed
    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_check_duplicate_reserved_version_stable(self, checkout_path):
        create_git_branch(self.repo, 'stable')
        create_git_tag(self.repo, 'stable')

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        version = self.project.versions.get(slug=LATEST)
        with self.assertRaises(RepositoryError) as e:
            sync_repository = sync_repository_task(version_id=version.pk)

        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        )

        # TODO: Check that we can build properly after
        # deleting the tag.

    def test_check_duplicate_no_reserved_version(self):
        create_git_branch(self.repo, 'no-reserved')
        create_git_tag(self.repo, 'no-reserved')

        version = self.project.versions.get(slug=LATEST)

        self.assertEqual(self.project.versions.filter(slug__startswith='no-reserved').count(), 0)

        sync_repository_task(version_id=version.pk)

        self.assertEqual(self.project.versions.filter(slug__startswith='no-reserved').count(), 2)

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
        self.assertEqual(
            result.info, {
                'task_name': 'public_task_exception',
                'context': {},
                'public_data': {},
                'error': 'Something bad happened',
            },
        )

    @patch('readthedocs.oauth.services.github.GitHubService.send_build_status')
    def test_send_build_status_with_remote_repo_github(self, send_build_status):
        self.project.repo = 'https://github.com/test/test/'
        self.project.save()

        social_account = get(SocialAccount, user=self.eric, provider='gitlab')
        remote_repo = get(RemoteRepository)
        remote_repo.projects.add(self.project)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.eric,
            account=social_account
        )

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            build=external_build,
            commit=external_build.commit,
            state=BUILD_STATUS_SUCCESS,
            link_to_build=False,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch('readthedocs.oauth.services.github.GitHubService.send_build_status')
    def test_send_build_status_with_social_account_github(self, send_build_status):
        social_account = get(SocialAccount, user=self.eric, provider='github')

        self.project.repo = 'https://github.com/test/test/'
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build, external_build.commit, BUILD_STATUS_SUCCESS
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch('readthedocs.oauth.services.github.GitHubService.send_build_status')
    def test_send_build_status_no_remote_repo_or_social_account_github(self, send_build_status):
        self.project.repo = 'https://github.com/test/test/'
        self.project.save()
        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_not_called()
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 1)

    @patch('readthedocs.oauth.services.gitlab.GitLabService.send_build_status')
    def test_send_build_status_with_remote_repo_gitlab(self, send_build_status):
        self.project.repo = 'https://gitlab.com/test/test/'
        self.project.save()

        social_account = get(SocialAccount, user=self.eric, provider='gitlab')
        remote_repo = get(RemoteRepository)
        remote_repo.projects.add(self.project)
        get(
            RemoteRepositoryRelation,
            remote_repository=remote_repo,
            user=self.eric,
            account=social_account
        )

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            build=external_build,
            commit=external_build.commit,
            state=BUILD_STATUS_SUCCESS,
            link_to_build=False,
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch('readthedocs.oauth.services.gitlab.GitLabService.send_build_status')
    def test_send_build_status_with_social_account_gitlab(self, send_build_status):
        social_account = get(SocialAccount, user=self.eric, provider='gitlab')

        self.project.repo = 'https://gitlab.com/test/test/'
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_called_once_with(
            external_build, external_build.commit, BUILD_STATUS_SUCCESS
        )
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 0)

    @patch('readthedocs.oauth.services.gitlab.GitLabService.send_build_status')
    def test_send_build_status_no_remote_repo_or_social_account_gitlab(self, send_build_status):
        self.project.repo = 'https://gitlab.com/test/test/'
        self.project.save()
        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        build_tasks.send_build_status(
            external_build.id, external_build.commit, BUILD_STATUS_SUCCESS
        )

        send_build_status.assert_not_called()
        self.assertEqual(Message.objects.filter(user=self.eric).count(), 1)

