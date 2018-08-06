# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from os import path

import mock
import pytest
import yaml
from django.test import TestCase
from django_dynamic_fixture import get
from mock import MagicMock, PropertyMock, patch

from readthedocs.builds.models import Version
from readthedocs.config import BuildConfigV1, InvalidConfig, ProjectConfig
from readthedocs.config.tests.utils import apply_fs
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.environments import LocalBuildEnvironment
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.projects import tasks
from readthedocs.projects.models import Feature, Project


def create_load(config=None):
    """
    Mock out the function of the build load function.

    This will create a ProjectConfig list of BuildConfigV1 objects and validate
    them. The default load function iterates over files and builds up a list of
    objects. Instead of mocking all of this, just mock the end result.
    """
    if config is None:
        config = {}

    def inner(path=None, env_config=None):
        env_config_defaults = {
            'output_base': '',
            'name': '1',
        }
        if env_config is not None:
            env_config_defaults.update(env_config)
        yaml_config = ProjectConfig([
            BuildConfigV1(
                env_config_defaults,
                config,
                source_file='readthedocs.yml',
                source_position=0,
            ),
        ])
        yaml_config.validate()
        return yaml_config

    return inner


@mock.patch('readthedocs.doc_builder.config.load_config')
class LoadConfigTests(TestCase):

    def setUp(self):
        self.project = get(
            Project,
            main_language_project=None,
            install_project=False,
            requirements_file='__init__.py'
        )
        self.version = get(Version, project=self.project)

    def test_python_supported_versions_default_image_1_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:1.0'
        self.project.enable_epub_build = True
        self.project.enable_pdf_build = True
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(load_config.call_count, 1)
        load_config.assert_has_calls([
            mock.call(
                path=mock.ANY,
                env_config={
                    'allow_v2': mock.ANY,
                    'build': {'image': 'readthedocs/build:1.0'},
                    'output_base': '',
                    'name': mock.ANY,
                    'defaults': {
                        'install_project': self.project.install_project,
                        'formats': [
                            'htmlzip',
                            'epub',
                            'pdf'
                        ],
                        'use_system_packages': self.project.use_system_packages,
                        'requirements_file': self.project.requirements_file,
                        'python_version': 2,
                        'sphinx_configuration': mock.ANY,
                        'build_image': 'readthedocs/build:1.0',
                        'doctype': self.project.documentation_type,
                    },
                },
            ),
        ])
        self.assertEqual(config.python.version, 2)

    def test_python_supported_versions_image_1_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:1.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.get_valid_python_versions(),
                         [2, 2.7, 3, 3.4])

    def test_python_supported_versions_image_2_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.get_valid_python_versions(),
                         [2, 2.7, 3, 3.5])

    def test_python_supported_versions_image_latest(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:latest'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.get_valid_python_versions(),
                         [2, 2.7, 3, 3.3, 3.4, 3.5, 3.6])

    def test_python_default_version(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, 2)
        self.assertEqual(config.python_interpreter, 'python2.7')

    def test_python_set_python_version_on_project(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.python_interpreter = 'python3'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, 3)
        self.assertEqual(config.python_interpreter, 'python3.5')

    def test_python_set_python_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 3.5},
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, 3.5)
        self.assertEqual(config.python_interpreter, 'python3.5')

    def test_python_invalid_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 2.6}
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        with self.assertRaises(InvalidConfig):
            load_yaml_config(self.version)

    def test_install_project(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(
            config.python.install_with_pip or config.python.install_with_setup,
            False
        )

        load_config.side_effect = create_load({
            'python': {'setup_py_install': True}
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.install_with_setup, True)

    def test_extra_requirements(self, load_config):
        load_config.side_effect = create_load({
            'python': {
                'pip_install': True,
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.extra_requirements, ['tests', 'docs'])

        load_config.side_effect = create_load({
            'python': {
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.extra_requirements, [])

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.extra_requirements, [])

        load_config.side_effect = create_load({
            'python': {
                'setup_py_install': True,
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.extra_requirements, [])

    def test_conda(self, load_config):
        to_find = '__init__.py'
        load_config.side_effect = create_load({
            'conda': {
                'file': to_find
            }
        })
        config = load_yaml_config(self.version)
        self.assertTrue(config.conda is not None)
        self.assertTrue(config.conda.environment[-len(to_find):] == to_find)

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertIsNone(config.conda)

    def test_requirements_file(self, load_config):
        requirements_file = '__init__.py'
        load_config.side_effect = create_load({
            'requirements_file': requirements_file
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.requirements, requirements_file)

        # Respects the requirements file from the project settings
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.requirements, '__init__.py')


@pytest.mark.django_db
@mock.patch('readthedocs.projects.models.Project.checkout_path')
class TestLoadConfigV2(object):

    @pytest.fixture(autouse=True)
    def create_project(self):
        self.project = get(
            Project,
            main_language_project=None,
            install_project=False,
            container_image=None,
        )
        self.version = get(Version, project=self.project)
        # TODO: Remove later
        get(
            Feature,
            projects=[self.project],
            feature_id=Feature.ALLOW_V2_CONFIG_FILE,
        )

    def create_config_file(self, tmpdir, config):
        base_path = apply_fs(tmpdir, {
            'readthedocs.yml': '',
        })
        config.setdefault('version', 2)
        config_file = path.join(str(base_path), 'readthedocs.yml')
        yaml.safe_dump(config, open(config_file, 'w'))
        return base_path

    def get_update_docs_task(self):
        build_env = LocalBuildEnvironment(
            self.project, self.version, record=False
        )

        update_docs = tasks.UpdateDocsTaskStep(
            build_env=build_env,
            config=load_yaml_config(self.version),
            project=self.project,
            version=self.version,
        )
        return update_docs

    def test_using_v2(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {})
        update_docs = self.get_update_docs_task()
        assert update_docs.config.version == '2'

    def test_report_using_invalid_version(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {'version': 12})
        with pytest.raises(InvalidConfig) as exinfo:
            self.get_update_docs_task()
        assert exinfo.value.key == 'version'

    @pytest.mark.parametrize('config', [{}, {'formats': []}])
    @patch('readthedocs.projects.models.Project.repo_nonblockinglock', new=MagicMock())
    @patch('readthedocs.doc_builder.backends.sphinx.SearchBuilder.build')
    @patch('readthedocs.doc_builder.backends.sphinx.HtmlBuilder.build')
    @patch('readthedocs.doc_builder.backends.sphinx.HtmlBuilder.append_conf')
    def test_build_formats_default_empty(
            self, append_conf, html_build, search_build,
            checkout_path, config, tmpdir):
        """
        The default value for formats is [], which means no extra
        formats are build.
        """
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, config)

        update_docs = self.get_update_docs_task()
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        outcomes = update_docs.build_docs()

        # No extra formats were triggered
        assert outcomes['html']
        assert outcomes['search']
        assert not outcomes['localmedia']
        assert not outcomes['pdf']
        assert not outcomes['epub']

    @patch('readthedocs.projects.models.Project.repo_nonblockinglock', new=MagicMock())
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs_class')
    @patch('readthedocs.doc_builder.backends.sphinx.SearchBuilder.build')
    @patch('readthedocs.doc_builder.backends.sphinx.HtmlBuilder.build')
    @patch('readthedocs.doc_builder.backends.sphinx.HtmlBuilder.append_conf')
    def test_build_formats_only_pdf(
            self, append_conf, html_build, search_build, build_docs_class,
            checkout_path, tmpdir):
        """
        Only the pdf format is build.
        """
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {'formats': ['pdf']})

        update_docs = self.get_update_docs_task()
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=update_docs.config
        )
        update_docs.python_env = python_env

        outcomes = update_docs.build_docs()

        # Only pdf extra format was triggered
        assert outcomes['html']
        assert outcomes['search']
        build_docs_class.assert_called_with('sphinx_pdf')
        assert outcomes['pdf']
        assert not outcomes['localmedia']
        assert not outcomes['epub']

    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.update_documentation_type', new=MagicMock())
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.setup_python_environment', new=MagicMock())
    @patch('readthedocs.projects.tasks.UpdateDocsTaskStep.build_docs', new=MagicMock())
    @patch('readthedocs.doc_builder.environments.BuildEnvironment.failed', new_callable=PropertyMock)
    def test_conda_environment(self, build_failed, checkout_path, tmpdir):
        build_failed.return_value = False
        checkout_path.return_value = str(tmpdir)
        conda_file = 'environmemt.yml'
        apply_fs(tmpdir, {conda_file: ''})
        base_path = self.create_config_file(
            tmpdir,
            {
                'conda': {'environment': conda_file}
            }
        )

        update_docs = self.get_update_docs_task()
        update_docs.run_build(docker=False, record=False)

        conda_file = path.join(str(base_path), conda_file)
        assert update_docs.config.conda.environment == conda_file
        assert isinstance(update_docs.python_env, Conda)

    def test_default_build_image(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        build_image = 'readthedocs/build:latest'
        self.create_config_file(tmpdir, {})
        update_docs = self.get_update_docs_task()
        assert update_docs.config.build.image == build_image

    def test_build_image(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        build_image = 'readthedocs/build:stable'
        self.create_config_file(
            tmpdir,
            {'build': {'image': 'stable'}},
        )
        update_docs = self.get_update_docs_task()
        assert update_docs.config.build.image == build_image

    def test_custom_build_image(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)

        build_image = 'readthedocs/build:3.0'
        self.project.container_image = build_image
        self.project.save()

        self.create_config_file(tmpdir, {})
        update_docs = self.get_update_docs_task()
        assert update_docs.config.build.image == build_image

    def test_python_version(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {})
        # The default version is always 3
        self.project.python_interpreter = 'python2'
        self.project.save()

        config = self.get_update_docs_task().config
        assert config.python.version == 3
        assert config.python_full_version == 3.6

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_python_requirements(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        requirements_file = 'requirements.txt'
        apply_fs(tmpdir, {requirements_file: ''})
        base_path = self.create_config_file(
            tmpdir,
            {
                'python': {'requirements': requirements_file}
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.install_user_requirements()

        args, kwargs = run.call_args
        requirements_file = path.join(str(base_path), requirements_file)

        assert config.python.requirements == requirements_file
        assert requirements_file in args

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_python_requirements_empty(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(
            tmpdir,
            {
                'python': {'requirements': ''}
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.install_user_requirements()

        assert config.python.requirements == ''
        assert not run.called

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_python_install_setup(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(
            tmpdir,
            {
                'python': {'install': 'setup.py'}
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.install_package()

        args, kwargs = run.call_args

        assert 'setup.py' in args
        assert 'install' in args
        assert config.python.install_with_setup
        assert not config.python.install_with_pip

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_python_install_pip(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(
            tmpdir,
            {
                'python': {'install': 'pip'}
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.install_package()

        args, kwargs = run.call_args

        assert 'setup.py' not in args
        assert 'install' in args
        assert config.python.install_with_pip
        assert not config.python.install_with_setup

    def test_python_install_project(self, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {})

        self.project.install_project = True
        self.project.save()

        config = self.get_update_docs_task().config

        assert config.python.install_with_setup
        assert not config.python.install_with_pip

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_python_extra_requirements(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(
            tmpdir,
            {
                'python': {
                    'install': 'pip',
                    'extra_requirements': ['docs'],
                }
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.install_package()

        args, kwargs = run.call_args

        assert 'setup.py' not in args
        assert 'install' in args
        assert '.[docs]' in args
        assert config.python.install_with_pip
        assert not config.python.install_with_setup

    @patch('readthedocs.doc_builder.environments.BuildEnvironment.run')
    def test_system_packages(self, run, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(
            tmpdir,
            {
                'python': {
                    'system_packages': True,
                }
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config

        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env
        update_docs.python_env.setup_base()

        args, kwargs = run.call_args

        assert '--system-site-packages' in args
        assert config.python.use_system_site_packages

    @pytest.mark.parametrize('value,result',
                             [('html', 'sphinx'),
                              ('htmldir', 'sphinx_htmldir'),
                              ('singlehtml', 'sphinx_singlehtml')])
    @patch('readthedocs.projects.tasks.get_builder_class')
    def test_sphinx_builder(
            self, get_builder_class, checkout_path, value, result, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {'sphinx': {'builder': value}})

        self.project.documentation_type = 'mkdocs'
        self.project.save()

        update_docs = self.get_update_docs_task()
        update_docs.build_docs_html()

        get_builder_class.assert_called_with(result)

    @patch('readthedocs.projects.tasks.get_builder_class')
    def test_sphinx_builder_default(
            self, get_builder_class, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        self.create_config_file(tmpdir, {})

        self.project.documentation_type = 'mkdocs'
        self.project.save()

        update_docs = self.get_update_docs_task()
        update_docs.build_docs_html()

        get_builder_class.assert_called_with('sphinx')

    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.move')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.append_conf')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.run')
    def test_sphinx_configuration_default(
            self, run, append_conf, move, checkout_path, tmpdir):
        """Should be default to find a conf.py file."""
        checkout_path.return_value = str(tmpdir)

        apply_fs(tmpdir, {'conf.py': ''})
        self.create_config_file(tmpdir, {})
        self.project.conf_py_file = ''
        self.project.save()

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert kwargs['cwd'] == str(tmpdir)
        append_conf.assert_called_once()
        move.assert_called_once()

    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.move')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.append_conf')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.run')
    def test_sphinx_configuration_default(
            self, run, append_conf, move, checkout_path, tmpdir):
        """Should be default to find a conf.py file."""
        checkout_path.return_value = str(tmpdir)

        apply_fs(tmpdir, {'conf.py': ''})
        self.create_config_file(tmpdir, {})
        self.project.conf_py_file = ''
        self.project.save()

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert kwargs['cwd'] == str(tmpdir)
        append_conf.assert_called_once()
        move.assert_called_once()

    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.move')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.append_conf')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.run')
    def test_sphinx_configuration(
            self, run, append_conf, move, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        apply_fs(tmpdir, {
            'conf.py': '',
            'docx': {
                'conf.py': '',
            },
        })
        self.create_config_file(
            tmpdir,
            {
                'sphinx': {
                    'configuration': 'docx/conf.py',
                },
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert kwargs['cwd'] == path.join(str(tmpdir), 'docx')
        append_conf.assert_called_once()
        move.assert_called_once()

    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.move')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.append_conf')
    @patch('readthedocs.doc_builder.backends.sphinx.BaseSphinx.run')
    def test_sphinx_fail_on_warning(
            self, run, append_conf, move, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        apply_fs(tmpdir, {
            'docx': {
                'conf.py': '',
            },
        })
        self.create_config_file(
            tmpdir,
            {
                'sphinx': {
                    'configuration': 'docx/conf.py',
                    'fail_on_warning': True,
                },
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert '-W' in args
        append_conf.assert_called_once()
        move.assert_called_once()

    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.move')
    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.append_conf')
    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.run')
    def test_mkdocs_configuration(
            self, run, append_conf, move, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        apply_fs(tmpdir, {
            'mkdocs.yml': '',
            'docx': {
                'mkdocs.yml': '',
            },
        })
        self.create_config_file(
            tmpdir,
            {
                'mkdocs': {
                    'configuration': 'docx/mkdocs.yml',
                },
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert '--config-file' in args
        assert path.join(str(tmpdir), 'docx/mkdocs.yml') in args
        append_conf.assert_called_once()
        move.assert_called_once()

    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.move')
    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.append_conf')
    @patch('readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.run')
    def test_mkdocs_fail_on_warning(
            self, run, append_conf, move, checkout_path, tmpdir):
        checkout_path.return_value = str(tmpdir)
        apply_fs(tmpdir, {
            'docx': {
                'mkdocs.yml': '',
            },
        })
        self.create_config_file(
            tmpdir,
            {
                'mkdocs': {
                    'configuration': 'docx/mkdocs.yml',
                    'fail_on_warning': True,
                },
            }
        )

        update_docs = self.get_update_docs_task()
        config = update_docs.config
        python_env = Virtualenv(
            version=self.version,
            build_env=update_docs.build_env,
            config=config
        )
        update_docs.python_env = python_env

        update_docs.build_docs_html()

        args, kwargs = run.call_args
        assert '--strict' in args
        append_conf.assert_called_once()
        move.assert_called_once()
