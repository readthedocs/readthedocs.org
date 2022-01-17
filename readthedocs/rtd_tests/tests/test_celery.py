import os
import shutil
from os.path import exists
from tempfile import mkdtemp
from unittest import mock
from unittest.mock import MagicMock, patch

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

        # Mock calls to API to return the objects we need
        mock.patch('readthedocs.projects.tasks.mixins.SyncRepositoryMixin.get_version', return_value=self.version).start()
        mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.get_project', return_value=self.project).start()
        mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.get_build', return_value={'id': 99, 'state': BUILD_STATE_TRIGGERED}).start()

    def tearDown(self):
        shutil.rmtree(self.repo)
        super().tearDown()

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    def test_update_docs(self):
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs')
    def test_update_docs_unexpected_setup_exception(self, mock_setup_vcs):
        exc = Exception()
        mock_setup_vcs.side_effect = exc
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs')
    def test_update_docs_unexpected_build_exception(self, mock_build_docs):
        exc = Exception()
        mock_build_docs.side_effect = exc
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.send_notifications')
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs')
    def test_no_notification_on_version_locked_error(self, mock_setup_vcs, mock_send_notifications):
        mock_setup_vcs.side_effect = VersionLockedError()

        version = self.project.versions.first()

        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )

        mock_send_notifications.assert_not_called()
        self.assertTrue(result.successful())

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    @patch('readthedocs.projects.tasks.utils.clean_build')
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs')
    def test_clean_build_after_update_docs(self, build_docs, clean_build):
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo) as mapi:
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.utils.clean_build')
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.run_setup')
    def test_clean_build_after_failure_in_update_docs(self, run_setup, clean_build):
        run_setup.side_effect = Exception()
        version = self.project.versions.first()
        build = get(
            Build, project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        clean_build.assert_called_with(version.pk)

    @patch('readthedocs.projects.tasks.mixins.api_v2')
    @patch('readthedocs.projects.tasks.mixins.SyncRepositoryMixin.get_version')
    @patch('readthedocs.projects.models.Project.checkout_path')
    def test_sync_repository(self, checkout_path, get_version, api_v2):
        # Create dir where to clone the repo
        local_repo = os.path.join(mkdtemp(), 'local')
        os.mkdir(local_repo)
        checkout_path.return_value = local_repo

        version = self.project.versions.get(slug=LATEST)
        get_version.return_value = version

        result = sync_repository_task(version.pk)
        self.assertTrue(result)

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

    @patch('readthedocs.builds.managers.log')
    def test_fileify_logging_when_wrong_version_pk(self, mock_logger):
        self.assertFalse(Version.objects.filter(pk=345343).exists())
        fileify(
            version_pk=345343,
            commit=None,
            build=1,
            search_ranking={},
            search_ignore=[],
        )
        mock_logger.warning.assert_called_with(
            'Version not found for given kwargs.',
            kwargs={'pk': 345343},
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

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_python_environment', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    @patch.object(BuildEnvironment, 'run')
    @patch('readthedocs.doc_builder.config.load_config')
    def test_install_apt_packages(self, load_config, run):
        config = BuildConfigV2(
            {},
            {
                'version': 2,
                'build': {
                    'apt_packages': [
                        'clangd',
                        'cmatrix',
                    ],
                },
            },
            source_file='readthedocs.yml',
        )
        config.validate()
        load_config.return_value = config

        version = self.project.versions.first()
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())

        self.assertEqual(run.call_count, 2)
        apt_update = run.call_args_list[0]
        apt_install = run.call_args_list[1]
        self.assertEqual(
            apt_update,
            mock.call(
                'apt-get',
                'update',
                '--assume-yes',
                '--quiet',
                user='root:root',
            )
        )
        self.assertEqual(
            apt_install,
            mock.call(
                'apt-get',
                'install',
                '--assume-yes',
                '--quiet',
                '--',
                'clangd',
                'cmatrix',
                user='root:root',
            )
        )

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    @patch.object(BuildEnvironment, 'run')
    @patch('readthedocs.doc_builder.config.load_config')
    def test_build_tools(self, load_config, build_run):
        config = BuildConfigV2(
            {},
            {
                'version': 2,
                'build': {
                    'os': 'ubuntu-20.04',
                    'tools': {
                        'python': '3.10',
                        'nodejs': '16',
                        'rust': '1.55',
                        'golang': '1.17',
                    },
                },
            },
            source_file='readthedocs.yml',
        )
        config.validate()
        load_config.return_value = config

        version = self.project.versions.first()
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())
        self.assertEqual(build_run.call_count, 14)

        python_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['python']['3.10']
        nodejs_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['nodejs']['16']
        rust_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['rust']['1.55']
        golang_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['golang']['1.17']
        self.assertEqual(
            build_run.call_args_list,
            [
                mock.call('asdf', 'install', 'python', python_version),
                mock.call('asdf', 'global', 'python', python_version),
                mock.call('asdf', 'reshim', 'python', record=False),
                mock.call('python', '-mpip', 'install', '-U', 'virtualenv', 'setuptools<58.3.0'),
                mock.call('asdf', 'install', 'nodejs', nodejs_version),
                mock.call('asdf', 'global', 'nodejs', nodejs_version),
                mock.call('asdf', 'reshim', 'nodejs', record=False),
                mock.call('asdf', 'install', 'rust', rust_version),
                mock.call('asdf', 'global', 'rust', rust_version),
                mock.call('asdf', 'reshim', 'rust', record=False),
                mock.call('asdf', 'install', 'golang', golang_version),
                mock.call('asdf', 'global', 'golang', golang_version),
                mock.call('asdf', 'reshim', 'golang', record=False),
                mock.ANY,
            ],
        )

    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs', new=MagicMock)
    @patch('readthedocs.projects.tasks.builds.UpdateDocsTask.setup_vcs', new=MagicMock)
    @patch('readthedocs.doc_builder.python_environments.tarfile')
    @patch('readthedocs.doc_builder.python_environments.build_tools_storage')
    @patch.object(BuildEnvironment, 'run')
    @patch('readthedocs.doc_builder.config.load_config')
    def test_build_tools_cached(self, load_config, build_run, build_tools_storage, tarfile):
        config = BuildConfigV2(
            {},
            {
                'version': 2,
                'build': {
                    'os': 'ubuntu-20.04',
                    'tools': {
                        'python': '3.10',
                        'nodejs': '16',
                        'rust': '1.55',
                        'golang': '1.17',
                    },
                },
            },
            source_file='readthedocs.yml',
        )
        config.validate()
        load_config.return_value = config

        build_tools_storage.open.return_value = b''
        build_tools_storage.exists.return_value = True
        tarfile.open.return_value.__enter__.return_value.extract_all.return_value = None

        version = self.project.versions.first()
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        with mock_api(self.repo):
            result = update_docs_task.delay(
                version.pk,
                build_pk=build.pk,
                record=False,
                intersphinx=False,
            )
        self.assertTrue(result.successful())
        self.assertEqual(build_run.call_count, 13)

        python_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['python']['3.10']
        nodejs_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['nodejs']['16']
        rust_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['rust']['1.55']
        golang_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['golang']['1.17']
        self.assertEqual(
            # NOTE: casting the first argument as `list()` shows a better diff
            # explaining where the problem is
            list(build_run.call_args_list),
            [
                mock.call(
                    'mv',
                    # Use mock.ANY here because path differs when ran locally
                    # and on CircleCI
                    mock.ANY,
                    f'/home/docs/.asdf/installs/python/{python_version}',
                    record=False,
                ),
                mock.call('asdf', 'global', 'python', python_version),
                mock.call('asdf', 'reshim', 'python', record=False),
                mock.call(
                    'mv',
                    mock.ANY,
                    f'/home/docs/.asdf/installs/nodejs/{nodejs_version}',
                    record=False,
                ),
                mock.call('asdf', 'global', 'nodejs', nodejs_version),
                mock.call('asdf', 'reshim', 'nodejs', record=False),
                mock.call(
                    'mv',
                    mock.ANY,
                    f'/home/docs/.asdf/installs/rust/{rust_version}',
                    record=False,
                ),
                mock.call('asdf', 'global', 'rust', rust_version),
                mock.call('asdf', 'reshim', 'rust', record=False),
                mock.call(
                    'mv',
                    mock.ANY,
                    f'/home/docs/.asdf/installs/golang/{golang_version}',
                    record=False,
                ),
                mock.call('asdf', 'global', 'golang', golang_version),
                mock.call('asdf', 'reshim', 'golang', record=False),
                mock.ANY,
            ],
        )
