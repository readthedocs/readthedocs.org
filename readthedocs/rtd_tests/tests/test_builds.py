from __future__ import absolute_import

import mock
import six

from django.test import TestCase
from django_dynamic_fixture import get
from django_dynamic_fixture import fixture

from readthedocs.projects.models import Project
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.doc_builder.loader import get_builder_class
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
        '''Test full build'''
        load_config.side_effect = create_load()
        project = get(Project,
                      slug='project-1',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      versions=[fixture()])
        version = project.versions.all()[0]
        self.mocks.configure_mock('api_versions', {'return_value': [version]})
        self.mocks.configure_mock('api', {
            'get.return_value': {'downloads': "no_url_here"}
        })
        self.mocks.patches['html_build'].stop()

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)
        task.build_docs()

        # Get command and check first part of command list is a call to sphinx
        self.assertEqual(self.mocks.popen.call_count, 3)
        cmd = self.mocks.popen.call_args_list[2][0]
        self.assertRegexpMatches(cmd[0][0], r'python')
        self.assertRegexpMatches(cmd[0][1], r'sphinx-build')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_pdf_flag(self, load_config):
        '''Build output format control'''
        load_config.side_effect = create_load()
        project = get(Project,
                      slug='project-1',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      enable_pdf_build=True,
                      enable_epub_build=False,
                      versions=[fixture()])
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)

        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.pdf_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.epub_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_epub_flag(self, load_config):
        '''Test build with epub enabled'''
        load_config.side_effect = create_load()
        project = get(Project,
                      slug='project-1',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      enable_pdf_build=False,
                      enable_epub_build=True,
                      versions=[fixture()])
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)
        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.epub_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.pdf_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_respects_yaml(self, load_config):
        '''Test YAML build options'''
        load_config.side_effect = create_load({'formats': ['epub']})
        project = get(Project,
                      slug='project-1',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      enable_pdf_build=False,
                      enable_epub_build=False,
                      versions=[fixture()])
        version = project.versions.all()[0]

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)

        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)
        task.build_docs()

        # The HTML and the Epub format were built.
        self.mocks.html_build.assert_called_once_with()
        self.mocks.epub_build.assert_called_once_with()
        # PDF however was disabled and therefore not built.
        self.assertFalse(self.mocks.pdf_build.called)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_pdf_latex_failures(self, load_config):
        '''Build failure if latex fails'''

        load_config.side_effect = create_load()
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = get(Project,
                      slug='project-1',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      enable_pdf_build=True,
                      enable_epub_build=False,
                      versions=[fixture()])
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            ((b'', b''), 0),  # sphinx-build html
            ((b'', b''), 0),  # sphinx-build pdf
            ((b'', b''), 1),  # latex
            ((b'', b''), 0),  # makeindex
            ((b'', b''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [output for (output, status)
                                            in returns]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns])
        self.mocks.popen.return_value = mock_obj

        with build_env:
            task.build_docs()
        self.assertEqual(self.mocks.popen.call_count, 7)
        self.assertTrue(build_env.failed)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_build_pdf_latex_not_failure(self, load_config):
        '''Test pass during PDF builds and bad latex failure status code'''

        load_config.side_effect = create_load()
        self.mocks.patches['html_build'].stop()
        self.mocks.patches['pdf_build'].stop()

        project = get(Project,
                      slug='project-2',
                      documentation_type='sphinx',
                      conf_py_file='test_conf.py',
                      enable_pdf_build=True,
                      enable_epub_build=False,
                      versions=[fixture()])
        version = project.versions.all()[0]
        assert project.conf_dir() == '/tmp/rtd'

        build_env = LocalBuildEnvironment(project=project, version=version, build={})
        python_env = Virtualenv(version=version, build_env=build_env)
        config = load_yaml_config(version)
        task = UpdateDocsTaskStep(build_env=build_env, project=project, python_env=python_env,
                              version=version, search=False, localmedia=False, config=config)

        # Mock out the separate calls to Popen using an iterable side_effect
        returns = [
            ((b'', b''), 0),  # sphinx-build html
            ((b'', b''), 0),  # sphinx-build pdf
            ((b'Output written on foo.pdf', b''), 1),  # latex
            ((b'', b''), 0),  # makeindex
            ((b'', b''), 0),  # latex
        ]
        mock_obj = mock.Mock()
        mock_obj.communicate.side_effect = [output for (output, status)
                                            in returns]
        type(mock_obj).returncode = mock.PropertyMock(
            side_effect=[status for (output, status) in returns])
        self.mocks.popen.return_value = mock_obj

        with build_env:
            task.build_docs()
        self.assertEqual(self.mocks.popen.call_count, 7)
        self.assertTrue(build_env.successful)
