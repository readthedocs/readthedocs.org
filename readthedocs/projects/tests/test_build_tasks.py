import os

from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
import django_dynamic_fixture as fixture

from readthedocs.builds.models import Build
from readthedocs.projects.models import EnvironmentVariable, Project
from readthedocs.projects.tasks.builds import UpdateDocsTask


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
