import os

from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
import django_dynamic_fixture as fixture

import pytest

from readthedocs.builds.constants import (
    BUILD_STATUS_FAILURE,
    BUILD_STATE_FINISHED,
    BUILD_STATUS_SUCCESS,
)
from readthedocs.builds.models import Build
from readthedocs.config import ConfigError, ALL
from readthedocs.config.config import BuildConfigV2
from readthedocs.doc_builder.exceptions import BuildEnvironmentError
from readthedocs.projects.models import EnvironmentVariable, Project, WebHookEvent
from readthedocs.projects.tasks.builds import UpdateDocsTask, update_docs_task

from .mockers import BuildEnvironmentMocker


@pytest.mark.django_db
class BuildEnvironmentBase:

    # NOTE: `load_yaml_config` maybe be moved to the setup and assign to self.

    @pytest.fixture(autouse=True)
    def setup(self, requests_mock):
        # Save the reference to query it from inside the test
        self.requests_mock = requests_mock

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

        self.mocker = BuildEnvironmentMocker(
            self.project,
            self.version,
            self.build,
            self.requests_mock,
        )
        self.mocker.start()

        yield

        # tearDown
        self.mocker.stop()

    def _trigger_update_docs_task(self):
        # NOTE: is it possible to replace calling this directly by `trigger_build` instead? :)
        return update_docs_task.delay(
            self.version.pk,
            build_pk=self.build.pk,

            # TODO: are these really required or can be completely removed from
            # our code?
            force=True,
            record=True,
        )

    def _config_file(self, config):
        config = BuildConfigV2(
            {},
            config,
            source_file='readthedocs.yaml',
        )
        config.validate()
        return config


class TestBuildTask(BuildEnvironmentBase):

    @pytest.mark.parametrize(
        'formats,build_class',
        (
            (['pdf'], ['sphinx_pdf']),
            (['htmlzip'], ['sphinx_singlehtmllocalmedia']),
            (['epub'], ['sphinx_epub']),
            (['pdf', 'htmlzip', 'epub'], ['sphinx_pdf', 'sphinx_singlehtmllocalmedia', 'sphinx_epub']),
        )
    )
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs_html')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs_class')
    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    @pytest.mark.skip
    def test_build_respects_formats_sphinx(self, build_docs_html, build_docs_class, load_yaml_config, formats, build_class):
        load_yaml_config.return_value = self._config_file({
            'version': 2,
            'formats': formats,
        })

        self._trigger_update_docs_task()

        build_docs_html.assert_called_once()

        for klass in build_class:
            build_docs_class.assert_called_once_with(klass)

    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs_html')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.build_docs_class')
    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_build_respects_formats_mkdocs(self, build_docs_html, build_docs_class, load_yaml_config):
        load_yaml_config.return_value = self._config_file({
            'version': 2,
            'mkdocs': {
                'configuration': 'mkdocs.yml',
            },
            'formats': ['epub', 'pdf'],
        })

        self._trigger_update_docs_task()

        build_docs_html.assert_called_once()
        build_docs_class.assert_not_called()


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    @pytest.mark.skip()
    # NOTE: find a way to test we are passing all the environment variables to all the commands
    def test_get_env_vars_default(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file({
            'version': 2,
        })

        fixture.get(
            EnvironmentVariable,
            name='TOKEN',
            value='a1b2c3',
            project=self.project,
        )

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

        self._trigger_update_docs_task()

        # mock this object to make sure that we are in a conda env
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

    @mock.patch('readthedocs.projects.tasks.builds.fileify')
    @mock.patch('readthedocs.projects.tasks.builds.build_complete')
    @mock.patch('readthedocs.projects.tasks.builds.send_external_build_status')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.send_notifications')
    @mock.patch('readthedocs.projects.tasks.builds.clean_build')
    def test_successful_build(self, clean_build, send_notifications, send_external_build_status, build_complete, fileify):
        self._trigger_update_docs_task()

        # It has to be called twice, ``before_start`` and ``after_return``
        clean_build.assert_has_calls([
            mock.call(mock.ANY),  # the argument is an APIVersion
            mock.call(mock.ANY)
        ])

        send_notifications.assert_called_once_with(
            self.version.pk,
            self.build.pk,
            event=WebHookEvent.BUILD_PASSED,
        )

        send_external_build_status.assert_called_once_with(
            version_type=self.version.type,
            build_pk=self.build.pk,
            commit=self.build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        build_complete.send.assert_called_once_with(
            sender=Build,
            build=mock.ANY,
        )

        fileify.delay.assert_called_once_with(
            version_pk=self.version.pk,
            commit=self.build.commit,
            build=self.build.pk,
            search_ranking=mock.ANY,
            search_ignore=mock.ANY,
        )

        # TODO: assert the verb and the path for each API call as well

        # Update build state: clonning
        assert self.requests_mock.request_history[3].json() == {
            'id': 1,
            'state': 'cloning',
            'commit': 'a1b2c3',
        }

        # Save config object data (using default values)
        assert self.requests_mock.request_history[4].json() == {
            'config': {
                'version': '1',
                'formats': [
                    'htmlzip',
                    'epub',
                    'pdf',
                ],
                'python': {
                    'version': '3',
                    'install': [{'requirements': None}],
                    'use_system_site_packages': False,
                },
                'conda': None,
                'build': {
                    'image': 'readthedocs/build:latest',
                    'apt_packages': [],
                },
                'doctype': 'sphinx',
                'sphinx': {
                    'builder': 'sphinx',
                    'configuration': None,
                    'fail_on_warning': False,
                },
                'mkdocs': {
                    'configuration': None,
                    'fail_on_warning': False,
                },
                'submodules': {
                    'include': 'all',
                    'exclude': [],
                    'recursive': True,
                },
                'search': {
                    'ranking': {},
                    'ignore': [],
                },
            },
        }
        # Update build state: installing
        assert self.requests_mock.request_history[5].json() == {
            'id': 1,
            'state': 'installing',
            'commit': 'a1b2c3',
            'config': mock.ANY,
        }
        # Update build state: building
        assert self.requests_mock.request_history[6].json() == {
            'id': 1,
            'state': 'building',
            'commit': 'a1b2c3',
            'config': mock.ANY,
        }
        # Pass active versions to build context
        assert (
            self.requests_mock.request_history[7].path == '/api/v2/project/1/active_versions/'
        )
        # Update build state: uploading
        assert self.requests_mock.request_history[9].json() == {
            'id': 1,
            'state': 'uploading',
            'commit': 'a1b2c3',
            'config': mock.ANY,
        }
        # Update version state
        assert self.requests_mock.request_history[10]._request.method == 'PATCH'
        assert self.requests_mock.request_history[10].path == '/api/v2/version/1/'
        assert self.requests_mock.request_history[10].json() == {
            'built': True,
            'documentation_type': 'sphinx',
            'has_pdf': True,
            'has_epub': True,
            'has_htmlzip': True,
        }
        # Set project has valid clone
        assert self.requests_mock.request_history[11]._request.method == 'PATCH'
        assert self.requests_mock.request_history[11].path == '/api/v2/project/1/'
        assert self.requests_mock.request_history[11].json() == {'has_valid_clone': True}
        # Update build state: finished, success and builder
        assert self.requests_mock.request_history[12].json() == {
            'id': 1,
            'state': 'finished',
            'commit': 'a1b2c3',
            'config': mock.ANY,
            'builder': mock.ANY,
            'length': mock.ANY,
            'success': True,
        }

        self.mocker.mocks['build_media_storage'].sync_directory.assert_has_calls([
            mock.call(mock.ANY, 'html/project/latest'),
            mock.call(mock.ANY, 'json/project/latest'),
            mock.call(mock.ANY, 'htmlzip/project/latest'),
            mock.call(mock.ANY, 'pdf/project/latest'),
            mock.call(mock.ANY, 'epub/project/latest'),
        ])
        # TODO: find a directory to remove here :)
        # build_media_storage.delete_directory

    @mock.patch('readthedocs.projects.tasks.builds.build_complete')
    @mock.patch('readthedocs.projects.tasks.builds.send_external_build_status')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.execute')
    @mock.patch('readthedocs.projects.tasks.builds.UpdateDocsTask.send_notifications')
    @mock.patch('readthedocs.projects.tasks.builds.clean_build')
    def test_failed_build(self, clean_build, send_notifications, execute, send_external_build_status, build_complete):
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
        api_request = self.requests_mock.request_history[-1]  # the last one should be the PATCH for the build
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

    def test_build_commands_executed(self):
        # NOTE: I didn't find a way to use the same ``requestsmock`` object for
        # all the tests and be able to put it on the setUp/tearDown
        self._trigger_update_docs_task()

        self.mocker.mocks['git.Backend.run'].assert_has_calls([
            mock.call('git', 'clone', '--no-single-branch', '--depth', '50', '', '.'),
            mock.call('git', 'checkout', '--force', 'a1b2c3'),
            mock.call('git', 'clean', '-d', '-f', '-f'),
        ])

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'python3.7',
                '-mvirtualenv',
                mock.ANY,
                bin_path=None,
                cwd=None,
            ),
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--no-cache-dir',
                'pip',
                'setuptools<58.3.0',
                bin_path=mock.ANY,
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                mock.ANY,
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
                bin_path=mock.ANY,
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                'cat',
                'conf.py',
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                mock.ANY,
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
                bin_path=mock.ANY,
            ),
            mock.call(
                mock.ANY,
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
                bin_path=mock.ANY,
            ),
            mock.call(
                mock.ANY,
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
                bin_path=mock.ANY,
            ),
            mock.call(
                mock.ANY,
                '-c',
                '"import sys; import sphinx; sys.exit(0 if sphinx.version_info >= (1, 6, 1) else 1)"',
                bin_path=mock.ANY,
                cwd='/tmp/readthedocs-tests/git-repository',
                escape_command=False,
                shell=True,
                record=False,
            ),
            mock.call(
                'mv',
                '-f',
                'output.file',
                mock.ANY,
                cwd='/tmp/readthedocs-tests/git-repository',
            ),
            mock.call(
                mock.ANY,
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
                bin_path=mock.ANY,
            ),
            mock.call(
                'mv',
                '-f',
                'output.file',
                mock.ANY,
                cwd='/tmp/readthedocs-tests/git-repository',
            )
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_use_config_file(self, load_yaml_config):
        self._trigger_update_docs_task()
        load_yaml_config.assert_called_once()

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_install_apt_packages(self, load_yaml_config):
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
        load_yaml_config.return_value = config

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'apt-get',
                'update',
                '--assume-yes',
                '--quiet',
                user='root:root',
            ),
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
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_build_tools(self, load_yaml_config):
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
        load_yaml_config.return_value = config

        self._trigger_update_docs_task()

        python_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['python']['3.10']
        nodejs_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['nodejs']['16']
        rust_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['rust']['1.55']
        golang_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['golang']['1.17']
        self.mocker.mocks['environment.run'].assert_has_calls([
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
        ])

    @mock.patch('readthedocs.doc_builder.python_environments.tarfile')
    @mock.patch('readthedocs.doc_builder.python_environments.build_tools_storage')
    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_build_tools_cached(self, load_yaml_config, build_tools_storage, tarfile):
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
        load_yaml_config.return_value = config

        build_tools_storage.open.return_value = b''
        build_tools_storage.exists.return_value = True
        tarfile.open.return_value.__enter__.return_value.extract_all.return_value = None

        self._trigger_update_docs_task()

        python_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['python']['3.10']
        nodejs_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['nodejs']['16']
        rust_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['rust']['1.55']
        golang_version = settings.RTD_DOCKER_BUILD_SETTINGS['tools']['golang']['1.17']
        self.mocker.mocks['environment.run'].assert_has_calls([
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
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_requirements_from_config_file_installed(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'install': [{
                        'requirements': 'requirements.txt',
                    }],
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--exists-action=w',
                '--no-cache-dir',
                '-r',
                'requirements.txt',
                cwd='/tmp/readthedocs-tests/git-repository',
                bin_path=mock.ANY,
            ),
        ])

    # TODO: migrate test_python_install_setuptools
    # TODO: migrate test_python_install_pip
    # TODO: migrate test_python_install_extra_requirements
    # TODO: migrate test_python_install_several_options
    # TODO: migrate test_system_packages

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_conda_config_calls_conda_command(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'conda': {
                    'environment': 'environment.yaml',
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'conda',
                'env',
                'create',
                '--quiet',
                '--name',
                self.version.slug,
                '--file',
                'environment.yaml',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
            mock.call(
                'conda',
                'install',
                '--yes',
                '--quiet',
                '--name',
                self.version.slug,
                'mock',
                'pillow',
                'sphinx',
                'sphinx_rtd_theme',
                cwd=mock.ANY,
            ),
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '-U',
                '--no-cache-dir',
                'recommonmark',
                'readthedocs-sphinx-ext',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_python_mamba_commands(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'build': {
                    'os': 'ubuntu-20.04',
                    'tools': {
                        'python': 'mambaforge-4.10',
                    },
                },
                'conda': {
                    'environment': 'environment.yaml',
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call('asdf', 'install', 'python', 'mambaforge-4.10.3-10'),
            mock.call('asdf', 'global', 'python', 'mambaforge-4.10.3-10'),
            mock.call('asdf', 'reshim', 'python', record=False),
            mock.call('mamba', 'env', 'create', '--quiet', '--name', 'latest', '--file', 'environment.yaml', bin_path=None, cwd=mock.ANY),
            mock.call('mamba', 'install', '--yes', '--quiet', '--name', 'latest', 'mock', 'pillow', 'sphinx', 'sphinx_rtd_theme', cwd=mock.ANY),
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_sphinx_fail_on_warning(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'sphinx': {
                    'configuration': 'docs/conf.py',
                    'fail_on_warning': True,
                    },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'sphinx',
                '-T',
                '-E',
                '-W',  # fail on warning flag
                '--keep-going',  # fail on warning flag
                '-b',
                'readthedocs',
                '-d',
                '_build/doctrees',
                '-D',
                'language=en',
                '.',
                '_build/html',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
        ])


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_mkdocs_fail_on_warning(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'mkdocs': {
                    'configuration': 'docs/mkdocs.yaml',
                    'fail_on_warning': True,
                    },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'mkdocs',
                'build',
                '--clean',
                '--site-dir',
                '_build/html',
                '--config-file',
                'docs/mkdocs.yaml',
                '--strict',  # fail on warning flag
                cwd=mock.ANY,
                bin_path=mock.ANY,
            )
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_system_site_packages(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'system_packages': True,
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'python3.7',
                '-mvirtualenv',
                '--system-site-packages',  # expected flag
                mock.ANY,
                bin_path=None,
                cwd=None,
            ),
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_system_site_packages_project_overrides(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                # Do not define `system_packages: True` in the config file.
                'python': {},
            },
        )

        # Override the setting in the Project object
        self.project.use_system_packages = True
        self.project.save()

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                'python3.7',
                '-mvirtualenv',
                # we don't expect this flag to be here
                # '--system-site-packages'
                mock.ANY,
                bin_path=None,
                cwd=None,
            ),
        ])


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_python_install_setuptools(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'setuptools',
                    }],
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                './setup.py',
                'install',
                '--force',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            )
        ])


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_python_install_pip(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                    }],
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--upgrade-strategy',
                'eager',
                '--no-cache-dir',
                '.',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            )
        ])


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_python_install_pip_extras(self, load_yaml_config):
        # FIXME: the test passes but in the logs there is an error related to
        # `backends/sphinx.py` not finding a file.
        #
        # TypeError('expected str, bytes or os.PathLike object, not NoneType')
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'install': [{
                        'path': '.',
                        'method': 'pip',
                        'extra_requirements': ['docs'],
                    }],
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--upgrade-strategy',
                'eager',
                '--no-cache-dir',
                '.[docs]',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            )
        ])


    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_python_install_pip_several_options(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'python': {
                    'install': [
                        {
                            'path': '.',
                            'method': 'pip',
                            'extra_requirements': ['docs'],
                        },
                        {
                            'path': 'two',
                            'method': 'setuptools',
                        },
                        {
                            'requirements': 'three.txt',
                        },
                    ],
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--upgrade',
                '--upgrade-strategy',
                'eager',
                '--no-cache-dir',
                '.[docs]',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
            mock.call(
                mock.ANY,
                'two/setup.py',
                'install',
                '--force',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
            mock.call(
                mock.ANY,
                '-m',
                'pip',
                'install',
                '--exists-action=w',
                '--no-cache-dir',
                '-r',
                'three.txt',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
        ])

    @pytest.mark.parametrize(
        'value,expected', [
            (ALL, ['one', 'two', 'three']),
            (['one', 'two'], ['one', 'two']),
        ],
    )
    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_submodules_include(self, load_yaml_config, value, expected):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'submodules': {
                    'include': value,
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['git.Backend.run'].assert_has_calls([
            mock.call('git', 'submodule', 'sync'),
            mock.call('git', 'submodule', 'update', '--init', '--force', *expected),
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_submodules_exclude(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'submodules': {
                    'exclude': ['one'],
                    'recursive': True
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['git.Backend.run'].assert_has_calls([
            mock.call('git', 'submodule', 'sync'),
            mock.call('git', 'submodule', 'update', '--init', '--force', '--recursive', 'two', 'three'),
        ])

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_submodules_exclude_all(self, load_yaml_config):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'submodules': {
                    'exclude': ALL,
                    'recursive': True
                },
            },
        )

        self._trigger_update_docs_task()

        # TODO: how do we do a assert_not_has_calls?
        # mock.call('git', 'submodule', 'sync'),
        # mock.call('git', 'submodule', 'update', '--init', '--force', 'one', 'two', 'three'),

        for call in self.mocker.mocks['git.Backend.run'].mock_calls:
            if 'submodule' in call.args:
                assert False, 'git submodule command found'


    @pytest.mark.parametrize(
        'value,command',
        [
            ('html', 'readthedocs'),
            ('htmldir', 'readthedocsdirhtml'),
            ('dirhtml', 'readthedocsdirhtml'),
            ('singlehtml', 'readthedocssinglehtml'),
        ],
    )
    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_sphinx_builder(self, load_yaml_config, value, command):
        load_yaml_config.return_value = self._config_file(
            {
                'version': 2,
                'sphinx': {
                    'builder': value,
                    'configuration': 'docs/conf.py',
                },
            },
        )

        self._trigger_update_docs_task()

        self.mocker.mocks['environment.run'].assert_has_calls([
            mock.call(
                mock.ANY,
                '-m',
                'sphinx',
                '-T',
                '-E',
                '-b',
                command,
                '-d',
                '_build/doctrees',
                '-D',
                'language=en',
                '.',
                '_build/html',
                cwd=mock.ANY,
                bin_path=mock.ANY,
            ),
        ])


class TestBuildTaskExceptionHandler(BuildEnvironmentBase):

    @mock.patch('readthedocs.projects.tasks.builds.load_yaml_config')
    def test_config_file_exception(self, load_yaml_config):
        load_yaml_config.side_effect = ConfigError(
            code='invalid',
            message='Invalid version in config file.'
        )
        self._trigger_update_docs_task()

        # This is a known exceptions. We hit the API saving the correct error
        # in the Build object. In this case, the "error message" coming from
        # the exception will be shown to the user
        assert self.requests_mock.request_history[-1]._request.method == 'PATCH'
        assert self.requests_mock.request_history[-1].path == '/api/v2/build/1/'
        assert self.requests_mock.request_history[-1].json() == {
            'id': 1,
            'state': 'finished',
            'commit': 'a1b2c3',
            'error': "Problem in your project's configuration. Invalid version in config file.",
            'success': False,
            'builder': mock.ANY,
            'length': 0,
        }


# - test command not recorded
# - test command recorded as success
# - test for docker
#   - assert we are calling the client on create, exec, kill, etc
#   - memory limit
#   - container id generation
#   - daemon connection failed (this is just BuildEnvironmentError) --no need for another test
#   - exception for docker API failure test (e.g. DockerAPIError)
#   - command not recorded
#   - command recorded as success
#   - container timeout


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
