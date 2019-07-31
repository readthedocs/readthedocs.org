import os
import shutil
from os.path import exists
from tempfile import mkdtemp

from django.contrib.auth.models import User
from django_dynamic_fixture import get
from mock import MagicMock, patch

from allauth.socialaccount.models import SocialAccount

from readthedocs.builds.constants import LATEST, BUILD_STATUS_SUCCESS, EXTERNAL
from readthedocs.builds.models import Build
from readthedocs.doc_builder.exceptions import VersionLockedError
from readthedocs.projects import tasks
from readthedocs.builds.models import Version
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RTDTestCase
from readthedocs.rtd_tests.mocks.mock_api import mock_api
from readthedocs.rtd_tests.utils import (
    create_git_branch,
    create_git_tag,
    delete_git_branch,
    make_test_git,
)


class TestCeleryBuilding(RTDTestCase):

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

    def tearDown(self):
        shutil.rmtree(self.repo)
        super().tearDown()

    def test_remove_dirs(self):
        directory = mkdtemp()
        self.assertTrue(exists(directory))
        result = tasks.remove_dirs.delay((directory,))
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    def test_clear_artifacts(self):
        version = self.project.versions.all()[0]
        directory = self.project.get_production_media_path(type_='pdf', version_slug=version.slug)
        os.makedirs(directory)
        self.assertTrue(exists(directory))
        result = tasks.remove_dirs.delay(paths=version.get_artifact_paths())
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

        directory = version.project.rtd_build_path(version=version.slug)
        os.makedirs(directory)
        self.assertTrue(exists(directory))
        result = tasks.remove_dirs.delay(paths=version.get_artifact_paths())
        self.assertTrue(result.successful())
        self.assertFalse(exists(directory))

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    def test_update_docs(self):
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.update_build', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs')
    def test_update_docs_unexpected_setup_exception(self, mock_setup_vcs):
        exc = Exception()
        mock_setup_vcs.side_effect = exc
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.update_build', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs')
    def test_update_docs_unexpected_build_exception(self, mock_build_docs):
        exc = Exception()
        mock_build_docs.side_effect = exc
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.send_notifications')
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs')
    def test_no_notification_on_version_locked_error(self, mock_setup_vcs, mock_send_notifications):
        mock_setup_vcs.side_effect = VersionLockedError()
        
        version = self.project.versions.first()

        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )

        mock_send_notifications.assert_not_called()
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_vcs', new=MagicMock)
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.update_build', new=MagicMock)
    @patch('readthedocs.projects.tasks.clean_build')
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs')
    def test_clean_build_after_update_docs(self, build_docs, clean_build):
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.clean_build')
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.run_setup')
    def test_clean_build_after_failure_in_update_docs(self, run_setup, clean_build):
        run_setup.side_effect = Exception()
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = tasks.update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        clean_build.assert_called_with(version.pk)

    def test_sync_repository(self):
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = tasks.sync_repository_task.delay(version.pk)
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.clean_build')
    def test_clean_build_after_sync_repository(self, clean_build):
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = tasks.sync_repository_task.delay(version.pk)
        self.assertTrue(result.successful())
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.SyncRepositoryTaskStep.run')
    @patch('readthedocs.projects.tasks.clean_build')
    def test_clean_build_after_failure_in_sync_repository(self, clean_build, run_syn_repository):
        run_syn_repository.side_effect = Exception()
        version = self.project.versions.get(slug=LATEST)
        with mock_api(self.repo):
            result = tasks.sync_repository_task.delay(version.pk)
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.api_v2')
    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_check_duplicate_reserved_version_latest(self, checkout_path, api_v2):
        create_git_branch(self.repo, 'latest')
        create_git_tag(self.repo, 'latest')

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        version = self.project.versions.get(slug=LATEST)
        sync_repository = tasks.UpdateDocsTaskStep()
        sync_repository.version = version
        sync_repository.project = self.project
        with self.assertRaises(RepositoryError) as e:
            sync_repository.sync_repo()
        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        )

        delete_git_branch(self.repo, 'latest')
        sync_repository.sync_repo()
        api_v2.project().sync_versions.post.assert_called()

    @patch('readthedocs.projects.tasks.api_v2')
    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_check_duplicate_reserved_version_stable(self, checkout_path, api_v2):
        create_git_branch(self.repo, 'stable')
        create_git_tag(self.repo, 'stable')

        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        version = self.project.versions.get(slug=LATEST)
        sync_repository = tasks.UpdateDocsTaskStep()
        sync_repository.version = version
        sync_repository.project = self.project
        with self.assertRaises(RepositoryError) as e:
            sync_repository.sync_repo()
        self.assertEqual(
            str(e.exception),
            RepositoryError.DUPLICATED_RESERVED_VERSIONS,
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
        self.assertEqual(
            result.info, {
                'task_name': 'public_task_exception',
                'context': {},
                'public_data': {},
                'error': 'Something bad happened',
            },
        )

    @patch('readthedocs.builds.managers.log')
    def test_sync_files_logging_when_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        tasks.sync_files(project_pk=None, version_pk=345343, doctype='sphinx')
        mock_logger.warning.assert_called_with("Version not found for given kwargs. {'pk': 345343}")

    @patch('readthedocs.builds.managers.log')
    def test_move_files_logging_when_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        tasks.move_files(version_pk=345343, hostname=None, doctype='sphinx')
        mock_logger.warning.assert_called_with("Version not found for given kwargs. {'pk': 345343}")

    @patch('readthedocs.builds.managers.log')
    def test_fileify_logging_when_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        tasks.fileify(version_pk=345343, commit=None, build=1)
        mock_logger.warning.assert_called_with("Version not found for given kwargs. {'pk': 345343}")

    @patch('readthedocs.projects.tasks.GitHubService.send_build_status')
    def test_send_build_status_task_with_remote_repo(self, send_build_status):
        social_account = get(SocialAccount, provider='github')
        remote_repo = get(RemoteRepository, account=social_account, project=self.project)
        remote_repo.users.add(self.eric)

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        tasks.send_build_status(external_build.id, BUILD_STATUS_SUCCESS)

        send_build_status.assert_called_once_with(external_build, BUILD_STATUS_SUCCESS)

    @patch('readthedocs.projects.tasks.GitHubService.send_build_status')
    def test_send_build_status_task_with_social_account(self, send_build_status):
        social_account = get(SocialAccount, user=self.eric, provider='github')

        self.project.repo = 'https://github.com/test/test/'
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        tasks.send_build_status(external_build.id, BUILD_STATUS_SUCCESS)

        send_build_status.assert_called_once_with(external_build, BUILD_STATUS_SUCCESS)

    @patch('readthedocs.projects.tasks.GitHubService.send_build_status')
    def test_send_build_status_task_without_remote_repo_or_social_account(self, send_build_status):
        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )
        tasks.send_build_status(external_build.id, BUILD_STATUS_SUCCESS)

        send_build_status.assert_not_called()
