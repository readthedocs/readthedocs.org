# -*- coding: utf-8 -*-
import datetime
import os

import mock
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import fixture, get
from django.utils import timezone

from allauth.socialaccount.models import SocialAccount

from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    GITHUB_EXTERNAL_VERSION_NAME,
    GENERIC_EXTERNAL_VERSION_NAME
)
from readthedocs.builds.models import Build, Version
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.oauth.models import RemoteRepository
from readthedocs.projects.models import EnvironmentVariable, Project
from readthedocs.projects.tasks import UpdateDocsTaskStep
from readthedocs.rtd_tests.tests.test_config_integration import create_load

from ..mocks.environment import EnvironmentMockGroup


class BuildEnvironmentTests(TestCase):

    def setUp(self):
        self.mocks = EnvironmentMockGroup()
        self.mocks.start()

    def tearDown(self):
        self.mocks.stop()

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build(self, load_config):
        """Test full build."""
        load_config.side_effect = create_load()
        project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            versions=[fixture()],
        )
        version = project.versions.all()[0]
        self.mocks.configure_mock('api_versions', {'return_value': [version]})
        self.mocks.configure_mock(
            'api', {
                'get.return_value': {'downloads': 'no_url_here'},
            },
        )
        self.mocks.patches['html_build'].stop()

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )
        task.build_docs()

        # Get command and check first part of command list is a call to sphinx
        self.assertEqual(self.mocks.popen.call_count, 3)
        cmd = self.mocks.popen.call_args_list[2][0]
        self.assertRegex(cmd[0][0], r'python')
        self.assertRegex(cmd[0][1], r'sphinx-build')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_pdf_flag(self, load_config):
        """Build output format control."""
        load_config.side_effect = create_load()
        project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            enable_pdf_build=True,
            enable_epub_build=False,
            versions=[fixture()],
        )
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )

        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.pdf_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.epub_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_dont_localmedia_build_pdf_epub_search_in_mkdocs(self, load_config):
        load_config.side_effect = create_load()
        project = get(
            Project,
            slug='project-1',
            documentation_type='mkdocs',
            enable_pdf_build=True,
            enable_epub_build=True,
            versions=[fixture()],
        )
        version = project.versions.all().first()

        build_env = LocalBuildEnvironment(
            project=project,
            version=version,
            build={},
        )
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )

        task.build_docs()

        # Only html for mkdocs was built
        self.mocks.html_build_mkdocs.assert_called_once()
        self.mocks.html_build.assert_not_called()
        self.mocks.localmedia_build.assert_not_called()
        self.mocks.pdf_build.assert_not_called()
        self.mocks.epub_build.assert_not_called()

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_epub_flag(self, load_config):
        """Test build with epub enabled."""
        load_config.side_effect = create_load()
        project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            enable_pdf_build=False,
            enable_epub_build=True,
            versions=[fixture()],
        )
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )
        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.epub_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.pdf_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_yaml(self, load_config):
        """Test YAML build options."""
        load_config.side_effect = create_load({'formats': ['epub']})
        project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            enable_pdf_build=False,
            enable_epub_build=False,
            versions=[fixture()],
        )
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)

        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )
        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.epub_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.pdf_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_pdf_latex_failures(self, load_config):
        """Build failure if latex fails."""

        load_config.side_effect = create_load()
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            enable_pdf_build=True,
            enable_epub_build=False,
            versions=[fixture()],
        )
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            ((b'', b''), 0),  # sphinx-build html
            ((b'', b''), 0),  # sphinx-build pdf
            ((b'', b''), 1),  # sphinx version check
            ((b'', b''), 1),  # latex
            ((b'', b''), 0),  # makeindex
            ((b'', b''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [
            output for (output, status)
            in returns
        ]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns],
        )
        self.mocks.popen.return_value = mock_obj

        with build_env:
            task.build_docs()
        self.assertEqual(self.mocks.popen.call_count, 8)
        self.assertTrue(build_env.failed)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_pdf_latex_not_failure(self, load_config):
        """Test pass during PDF builds and bad latex failure status code."""

        load_config.side_effect = create_load()
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = get(
            Project,
            slug='project-2',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            enable_pdf_build=True,
            enable_epub_build=False,
            versions=[fixture()],
        )
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(
            build_env=build_env, project=project, python_env=python_env,
            version=version, config=config,
        )

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            ((b'', b''), 0),  # sphinx-build html
            ((b'', b''), 0),  # sphinx-build pdf
            ((b'', b''), 1),  # sphinx version check
            ((b'Output written on foo.pdf', b''), 1),  # latex
            ((b'', b''), 0),  # makeindex
            ((b'', b''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [
            output for (output, status)
            in returns
        ]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns],
        )
        self.mocks.popen.return_value = mock_obj

        with build_env:
            task.build_docs()
        self.assertEqual(self.mocks.popen.call_count, 8)
        self.assertTrue(build_env.successful)

    @mock.patch('readthedocs.projects.tasks.api_v2')
    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_save_config_in_build_model(self, load_config, api_v2):
        load_config.side_effect = create_load()
        api_v2.build.get.return_value = {}
        project = get(
            Project,
            slug='project',
            documentation_type='sphinx',
        )
        build = get(Build)
        version = get(Version, slug='1.8', project=project)
        task = UpdateDocsTaskStep(
            project=project, version=version, build={'id': build.pk},
        )
        task.setup_vcs = mock.Mock()
        task.run_setup()
        build_config = task.build['config']
        # For patch
        api_v2.build.assert_called_once()
        assert build_config['version'] == '1'
        assert 'sphinx' in build_config
        assert build_config['doctype'] == 'sphinx'

    def test_get_env_vars(self):
        project = get(
            Project,
            slug='project',
            documentation_type='sphinx',
        )
        get(
            EnvironmentVariable,
            name='TOKEN',
            value='a1b2c3',
            project=project,
        )
        build = get(Build)
        version = get(Version, slug='1.8', project=project)
        task = UpdateDocsTaskStep(
            project=project, version=version, build={'id': build.pk},
        )

        # mock this object to make sure that we are NOT in a conda env
        task.config = mock.Mock(conda=None)

        env = {
            'READTHEDOCS': True,
            'READTHEDOCS_VERSION': version.slug,
            'READTHEDOCS_PROJECT': project.slug,
            'READTHEDOCS_LANGUAGE': project.language,
            'BIN_PATH': os.path.join(
                project.doc_path,
                'envs',
                version.slug,
                'bin',
            ),
            'TOKEN': 'a1b2c3',
        }
        self.assertEqual(task.get_env_vars(), env)

        # mock this object to make sure that we are in a conda env
        task.config = mock.Mock(conda=True)
        env.update({
            'CONDA_ENVS_PATH': os.path.join(project.doc_path, 'conda'),
            'CONDA_DEFAULT_ENV': version.slug,
            'BIN_PATH': os.path.join(
                project.doc_path,
                'conda',
                version.slug,
                'bin',
            ),
        })
        self.assertEqual(task.get_env_vars(), env)


class BuildModelTests(TestCase):

    fixtures = ['test_data']

    def setUp(self):
        self.eric = User(username='eric')
        self.eric.set_password('test')
        self.eric.save()

        self.project = get(Project)
        self.project.users.add(self.eric)
        self.version = get(Version, project=self.project)

        self.pip = Project.objects.get(slug='pip')
        self.external_version = get(
            Version,
            identifier='9F86D081884C7D659A2FEAA0C55AD015A',
            verbose_name='9999',
            slug='pr-9999',
            project=self.pip,
            active=True,
            type=EXTERNAL
        )
        self.pip_version = get(
            Version,
            identifier='origin/stable',
            verbose_name='stable',
            slug='stable',
            project=self.pip,
            active=True,
            type=BRANCH
        )

    def test_get_previous_build(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1},
        )
        build_two = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 2},
        )
        build_three = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 3},
            success=False,
        )

        self.assertIsNone(build_one.previous)
        self.assertEqual(build_two.previous, build_one)
        self.assertEqual(build_three.previous, build_two)
        self.assertEqual(build_three.previous.previous, build_one)

    def test_normal_save_config(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build.config = {'version': 1}
        build.save()
        self.assertEqual(build.config, {'version': 1})

        build.config = {'version': 2}
        build.save()
        self.assertEqual(build.config, {'version': 2})

    def test_save_same_config(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {'version': 2}
        build_two.save()

        self.assertEqual(build_two.config, {'version': 2})

    def test_save_same_config_previous_empty(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {}
        build_two.save()

        self.assertEqual(build_two.config, {})
        build_two.config = {'version': 2}
        build_two.save()
        self.assertEqual(build_two.config, {'version': 2})

    def test_do_not_save_same_config(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {'version': 1}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {'version': 1}
        build_two.save()
        self.assertEqual(build_two._config, {Build.CONFIG_KEY: build_one.pk})
        self.assertEqual(build_two.config, {'version': 1})

    def test_do_not_save_same_config_nested(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {'version': 1}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {'version': 1}
        build_two.save()

        build_three = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_three.config = {'version': 1}
        build_three.save()

        build_four = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_four.config = {'version': 2}
        build_four.save()

        self.assertEqual(build_one.config, {'version': 1})
        self.assertEqual(build_one._config, {'version': 1})

        self.assertEqual(build_two._config, {Build.CONFIG_KEY: build_one.pk})
        self.assertEqual(build_three._config, {Build.CONFIG_KEY: build_one.pk})

        self.assertEqual(build_two.config, {'version': 1})
        self.assertEqual(build_three.config, {'version': 1})

        self.assertEqual(build_four.config, {'version': 2})
        self.assertEqual(build_four._config, {'version': 2})

    def test_do_not_reference_empty_configs(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {}
        build_two.save()
        self.assertEqual(build_two._config, {})
        self.assertEqual(build_two.config, {})

    def test_build_is_stale(self):
        now = timezone.now()

        build_one = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=8),
            state='finished'
        )
        build_two = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=6),
            state='triggered'
        )
        build_three = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=2),
            state='triggered'
        )

        self.assertFalse(build_one.is_stale)
        self.assertTrue(build_two.is_stale)
        self.assertFalse(build_three.is_stale)

    def test_using_latest_config(self):
        now = timezone.now()

        build = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=8),
            state='finished',
        )

        self.assertFalse(build.using_latest_config())

        build.config = {'version': 2}
        build.save()

        self.assertTrue(build.using_latest_config())

    def test_build_is_external(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1},
        )

        self.assertTrue(external_build.is_external)

    def test_build_is_not_external(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1},
        )

        self.assertFalse(build.is_external)

    def test_no_external_version_name(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1},
        )

        self.assertEqual(build.external_version_name, None)

    def test_external_version_name_github(self):
        self.project.repo = 'https://github.com/test/test/'
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(
            Build, project=self.project, version=external_version
        )

        self.assertEqual(
            external_build.external_version_name,
            GITHUB_EXTERNAL_VERSION_NAME
        )

    def test_external_version_name_generic(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            config={'version': 1},
        )

        self.assertEqual(
            external_build.external_version_name,
            GENERIC_EXTERNAL_VERSION_NAME
        )

    def test_get_commit_url_external_version_github(self):

        external_build = get(
            Build,
            project=self.pip,
            version=self.external_version,
            config={'version': 1},
        )
        expected_url = 'https://github.com/pypa/pip/pull/{number}/commits/{sha}'.format(
            number=self.external_version.verbose_name,
            sha=external_build.commit
        )
        self.assertEqual(external_build.get_commit_url(), expected_url)

    def test_get_commit_url_internal_version(self):
        build = get(
            Build,
            project=self.pip,
            version=self.pip_version,
            config={'version': 1},
        )
        expected_url = 'https://github.com/pypa/pip/commit/{sha}'.format(
            sha=build.commit
        )
        self.assertEqual(build.get_commit_url(), expected_url)
