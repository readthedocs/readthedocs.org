import os

from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
import django_dynamic_fixture as fixture

import requests_mock

from readthedocs.builds.constants import BUILD_STATUS_FAILURE, BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.projects.models import EnvironmentVariable, Project, WebHookEvent
from readthedocs.projects.tasks.builds import UpdateDocsTask, update_docs_task

from .mockers import BuildEnvironmentMocker


# NOTE: some of these tests where moved from `rtd_tests/test_builds.py` and
# adapted to work with the new approach.
class BuildTaskTests(TestCase):

    def setUp(self):
        self.project = fixture.get(
            Project,
            slug='project',
        )
        self.version = self.project.versions.get(slug='latest')
        self.build = fixture.get(
            Build,
            version=self.version,
        )

    @mock.patch.object(UpdateDocsTask, 'update_build' , mock.MagicMock())
    @mock.patch.object(UpdateDocsTask, 'build_docs_html' , mock.MagicMock())
    @mock.patch.object(UpdateDocsTask, 'build_docs_class')
    def test_build_respects_formats_sphinx(self, build_docs_class):
        task = UpdateDocsTask()
        task.project = self.project
        task.version = self.version


        # Mock config object
        config = mock.MagicMock(
            doctype='sphinx',
        )
        task.config = config

        # TODO: check that HTML output is being called in all the cases.

        # PDF
        config.formats = ['pdf']
        task.build_docs()
        build_docs_class.assert_called_once_with('sphinx_pdf')
        build_docs_class.reset_mock()

        # HTML Zip
        config.formats = ['htmlzip']
        task.build_docs()
        build_docs_class.assert_called_once_with('sphinx_singlehtmllocalmedia')
        build_docs_class.reset_mock()

        # ePub
        config.formats = ['epub']
        task.build_docs()
        build_docs_class.assert_called_once_with('sphinx_epub')
        build_docs_class.reset_mock()

    @mock.patch.object(UpdateDocsTask, 'update_build' , mock.MagicMock())
    @mock.patch.object(UpdateDocsTask, 'build_docs_html' , mock.MagicMock())
    @mock.patch.object(UpdateDocsTask, 'build_docs_class')
    def test_build_respects_formats_mkdocs(self, build_docs_class):
        task = UpdateDocsTask()
        task.project = self.project
        task.version = self.version

        # Mock config object
        config = mock.MagicMock(
            doctype='mkdocs',
            formats=['pdf', 'htmlzip', 'epub'],
        )
        task.config = config
        task.build_docs()
        build_docs_class.assert_not_called()

    @mock.patch.object(UpdateDocsTask, 'update_vcs_submodules', mock.MagicMock())
    @mock.patch('readthedocs.projects.tasks.builds.api_v2')
    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_save_build_config(self, load_config, api_v2):

        # NOTE: load a minimal config file into memory without using the file system
        from readthedocs.rtd_tests.tests.test_config_integration import create_load
        load_config.side_effect = create_load()

        task = UpdateDocsTask()
        task.project = self.project
        task.version = self.version
        task.build = {'id': self.build.pk}

        task.environment_class = mock.MagicMock()
        task.setup_vcs = mock.MagicMock()
        task.run_setup()

        # We call the API to save the build object
        api_v2.build(self.build.pk).patch.assert_called_once_with({'config': mock.ANY})

        # We update the task object with the current config
        self.assertEqual(task.build['config']['version'], '1')
        self.assertEqual(task.build['config']['doctype'], 'sphinx')

    def test_get_env_vars(self):
        fixture.get(
            EnvironmentVariable,
            name='TOKEN',
            value='a1b2c3',
            project=self.project,
        )
        task = UpdateDocsTask()

        task.project = self.project
        task.version = self.version
        task.build = {'id': self.build.pk}

        # mock this object to make sure that we are NOT in a conda env
        task.config = mock.Mock(conda=None)

        env = {
            'NO_COLOR': '1',
            'READTHEDOCS': 'True',
            'READTHEDOCS_VERSION': self.version.slug,
            'READTHEDOCS_PROJECT': self.project.slug,
            'READTHEDOCS_LANGUAGE': self.project.language,
            'BIN_PATH': os.path.join(
                self.project.doc_path,
                'envs',
                self.version.slug,
                'bin',
            ),
            'TOKEN': 'a1b2c3',
        }
        self.assertEqual(task.get_build_env_vars(), env)

        # mock this object to make sure that we are in a conda env
        task.config = mock.Mock(conda=True)
        env.update({
            'CONDA_ENVS_PATH': os.path.join(self.project.doc_path, 'conda'),
            'CONDA_DEFAULT_ENV': self.version.slug,
            'BIN_PATH': os.path.join(
                self.project.doc_path,
                'conda',
                self.version.slug,
                'bin',
            ),
        })
        self.assertEqual(task.get_build_env_vars(), env)


# NOTE: these are most of the tests coming from `rtd_tests/test_celery.py`
#
# Move them to the previous class, since, in theory are related to the build
# process and should mock most of it just to check the integrations.
@requests_mock.Mocker()
class CeleryBuildTest(TestCase):

    # - handle unexpected exception at `run_setup`
    # - handle unexpected exception at `run_build`
    # - version locked does not send notification
    # - `clean_build` is called after `sync_repository_task`
    # - `clean_build` is called after `sync_repository_task` even if it fails
    # - check duplicate reserved versions -requires integration (called by our task) and unit-test (raise expecetd exception). This is for `latest`, `stable` and `non-reserverd` (regular) versions
    # - public task exception (not related with the build process)
    # - test we call `send_build_status` with (and without) remote repository associated to the project
    # - test we don't call `send_build_status` if no remote repository nor account is associated
    # - (same that previous for gitlab, but not for bitbucket :) )
    # - assert we call `apt-get install` when using `build.apt_packages` config file
    # - assert we call `asdf install python` and more when using `build.tools` in config file
    # - assert we call only `asdf global python` if it's cached in the bucket

    def setUp(self):
        self.project = fixture.get(
            Project,
            slug='project',
            enable_epub_build=True,
            enable_pdf_build=True,
        )
        self.version = self.project.versions.get(slug='latest')
        self.build = fixture.get(
            Build,
            version=self.version,
            commit='a1b2c3',
        )

    def _trigger_update_docs_task(self):
        return update_docs_task.delay(
            self.version.pk,
            build_pk=self.build.pk,

            # TODO: are these really required or can be completely removed from
            # our code?
            force=True,
            record=True,
        )

    @mock.patch('readthedocs.projects.tasks.builds.build_complete')
    @mock.patch('readthedocs.projects.tasks.builds.send_external_build_status')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.execute')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.send_notifications')
    @mock.patch('readthedocs.projects.tasks.builds.clean_build')
    def test_failed_build(self, requestsmock, clean_build, send_notifications, execute, send_external_build_status, build_complete):
        mocker = BuildEnvironmentMocker(self.project, self.version, self.build, requestsmock)
        mocker.start()

        execute.side_effect = Exception('Force and exception here.')
        self._trigger_update_docs_task()


        # It has to be called twice, ``before_start`` and ``after_return``
        clean_build.assert_has_calls([
            mock.call(mock.ANY),  # the argument is an APIVersion
            mock.call(mock.ANY)
        ])

        send_notifications.assert_called_once_with(
            self.version.pk,
            self.build.pk,
            event=WebHookEvent.BUILD_FAILED,
        )

        send_external_build_status.assert_called_once_with(
            version_type=self.version.type,
            build_pk=self.build.pk,
            commit=self.build.commit,
            status=BUILD_STATUS_FAILURE,
        )

        build_complete.send.assert_called_once_with(
            sender=Build,
            build=mock.ANY,
        )

        # Test we are updating the DB by calling the API with the updated build object
        api_request = requestsmock.request_history[-1]  # the last one should be the PATCH for the build
        assert api_request._request.method == 'PATCH'
        assert api_request.json() == {
            'builder': mock.ANY,
            'commit': self.build.commit,
            'error': BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(build_id=self.build.pk),
            'id': self.build.pk,
            'length': mock.ANY,
            'state': 'finished',
            'success': False,
        }

    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.execute')
    @mock.patch('readthedocs.projects.tasks.builds.clean_build')
    def test_clean_build_called_when_build_fails(self, requestsmock, clean_build, execute):
        mocker = BuildEnvironmentMocker(self.project, self.version, self.build, requestsmock)
        mocker.start()

        execute.side_effect = Exception('Force and exception here.')
        self._trigger_update_docs_task()

    @mock.patch('readthedocs.projects.tasks.builds.clean_build')
    def test_clean_build_called(self, requestsmock, clean_build):
        mocker = BuildEnvironmentMocker(self.project, self.version, self.build, requestsmock)
        mocker.start()

        self._trigger_update_docs_task()

        # It has to be called twice, ``before_start`` and ``after_return``
        clean_build.assert_has_calls([
            mock.call(mock.ANY),  # the argument is an APIVersion
            mock.call(mock.ANY)
        ])

    def test_build_commands_executed(self, requestsmock):
        # NOTE: I didn't find a way to use the same ``requestsmock`` object for
        # all the tests and be able to put it on the setUp/tearDown
        mocker = BuildEnvironmentMocker(self.project, self.version, self.build, requestsmock)
        mocker.start()

        self._trigger_update_docs_task()

        mocker.mocks['git.Backend.run'].assert_has_calls([
            mock.call('git', 'clone', '--no-single-branch', '--depth', '50', '', '.'),
            mock.call('git', 'checkout', '--force', 'a1b2c3'),
            mock.call('git', 'clean', '-d', '-f', '-f'),
            mock.call('git', 'rev-parse', 'HEAD', record=False),
        ])

        mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'python3.7',
                '-mvirtualenv',
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest',
                bin_path=None,
                cwd=None,
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--no-cache-dir',
                'pip',
                'setuptools<58.3.0',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--no-cache-dir',
                'mock==1.0.1',
                'pillow==5.4.1',
                'alabaster>=0.7,<0.8,!=0.7.5',
                'commonmark==0.8.1',
                'recommonmark==0.5.0',
                'sphinx<2',
                'sphinx-rtd-theme<0.5',
                'readthedocs-sphinx-ext<2.2',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                'cat',
                'conf.py',
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'sphinx',
                '-T',
                '-E',
                '-b',
                'readthedocs',
                '-d',
                '_build/doctrees',
                '-D',
                'language=en',
                '.',
                '_build/html',
                cwd='/tmp/readthedocs-tests/git-repository',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'sphinx',
                '-T',
                '-b',
                'readthedocssinglehtmllocalmedia',
                '-d',
                '_build/doctrees',
                '-D',
                'language=en',
                '.',
                '_build/localmedia',
                cwd='/tmp/readthedocs-tests/git-repository',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'sphinx',
                '-b',
                'latex',
                '-D',
                'language=en',
                '-d', '_build/doctrees',
                '.',
                '_build/latex',
                cwd='/tmp/readthedocs-tests/git-repository',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-c',
                '"import sys; import sphinx; sys.exit(0 if sphinx.version_info >= (1, 6, 1) else 1)"',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
                cwd='/tmp/readthedocs-tests/git-repository',
                escape_command=False,
                shell=True,
                record=False,
            ),
            mock.call(
                'mv',
                '-f',
                'output.file',
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/artifacts/latest/sphinx_pdf/project.pdf',
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin/python',
                '-m',
                'sphinx',
                '-T',
                '-b',
                'epub',
                '-d',
                '_build/doctrees',
                '-D',
                'language=en',
                '.',
                '_build/epub',
                cwd='/tmp/readthedocs-tests/git-repository',
                bin_path='/usr/src/app/checkouts/readthedocs.org/user_builds/project/envs/latest/bin',
            ),
            mock.call(
                'mv',
                '-f',
                'output.file',
                '/usr/src/app/checkouts/readthedocs.org/user_builds/project/artifacts/latest/sphinx_epub/project.epub',
                cwd='/tmp/readthedocs-tests/git-repository',
            )
        ])
