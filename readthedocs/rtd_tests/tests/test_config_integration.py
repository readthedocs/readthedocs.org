import tempfile
from os import path

from unittest import mock
import yaml
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.config import (
    SETUPTOOLS,
    BuildConfigV1,
    InvalidConfig,
)
from readthedocs.config.models import PythonInstallRequirements
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.constants import DOCKER_IMAGE_SETTINGS
from readthedocs.projects.models import Project


def create_load(config=None):
    """
    Mock out the function of the build load function.

    This will create a BuildConfigV1 object and validate it.
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
        yaml_config = BuildConfigV1(
            env_config_defaults,
            config,
            source_file='readthedocs.yml',
        )
        yaml_config.validate()
        return yaml_config

    return inner


def create_config_file(config, file_name='readthedocs.yml', base_path=None):
    """
    Creates a readthedocs configuration file with name
    ``file_name`` in ``base_path``. If ``base_path`` is not given
    a temporal directory is created.
    """
    if not base_path:
        base_path = tempfile.mkdtemp()
    full_path = path.join(base_path, file_name)
    yaml.safe_dump(config, open(full_path, 'w'))
    return full_path


class LoadConfigTests(TestCase):

    def setUp(self):
        self.project = get(
            Project,
            main_language_project=None,
            install_project=False,
            container_image=None,
        )
        self.version = get(Version, project=self.project)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_supported_versions_default_image_1_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:1.0'
        self.project.enable_epub_build = True
        self.project.enable_pdf_build = True
        self.project.save()
        config = load_yaml_config(self.version)

        expected_env_config = {
            'build': {'image': 'readthedocs/build:1.0'},
            'defaults': {
                'install_project': self.project.install_project,
                'formats': [
                    'htmlzip',
                    'epub',
                    'pdf'
                ],
                'use_system_packages': self.project.use_system_packages,
                'requirements_file': self.project.requirements_file,
                'python_version': '3',
                'sphinx_configuration': mock.ANY,
                'build_image': 'readthedocs/build:1.0',
                'doctype': self.project.documentation_type,
            },
        }

        img_settings = DOCKER_IMAGE_SETTINGS.get(self.project.container_image, None)
        if img_settings:
            expected_env_config.update(img_settings)

        load_config.assert_called_once_with(
                path=mock.ANY,
                env_config=expected_env_config,
        )
        self.assertEqual(config.python.version, '3')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_supported_versions_image_2_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(
            config.get_valid_python_versions(),
            ['2', '2.7', '3', '3.5'],
        )

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_supported_versions_image_latest(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:latest'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(
            config.get_valid_python_versions(),
            ['2', '2.7', '3', '3.5', '3.6', '3.7', '3.8', 'pypy3.5'],
        )

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_default_version(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, '3')
        self.assertEqual(config.python_interpreter, 'python3.7')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_set_python_version_on_project(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.python_interpreter = 'python3'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, '3')
        self.assertEqual(config.python_interpreter, 'python3.5')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_set_python_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 3.5},
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, '3.5')
        self.assertEqual(config.python_interpreter, 'python3.5')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_set_python_310_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'build': {'image': 'testing'},
            'python': {'version': '3.10'},
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.python.version, '3.10')
        self.assertEqual(config.python_interpreter, 'python3.10')

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_python_invalid_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 2.6},
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        with self.assertRaises(InvalidConfig):
            load_yaml_config(self.version)

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_install_project(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 1)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )

        load_config.side_effect = create_load({
            'python': {'setup_py_install': True},
        })
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 2)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )
        self.assertEqual(
            config.python.install[1].method,
            SETUPTOOLS
        )

    @mock.patch('readthedocs.doc_builder.config.load_config')
    def test_extra_requirements(self, load_config):
        load_config.side_effect = create_load({
            'python': {
                'pip_install': True,
                'extra_requirements': ['tests', 'docs'],
            },
        })
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 2)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )
        self.assertEqual(
            config.python.install[1].extra_requirements,
            ['tests', 'docs']
        )

        load_config.side_effect = create_load({
            'python': {
                'extra_requirements': ['tests', 'docs'],
            },
        })
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 1)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 1)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )

        load_config.side_effect = create_load({
            'python': {
                'setup_py_install': True,
                'extra_requirements': ['tests', 'docs'],
            },
        })
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 2)
        self.assertTrue(
            isinstance(config.python.install[0], PythonInstallRequirements)
        )
        self.assertEqual(
            config.python.install[1].extra_requirements,
            []
        )

    @mock.patch('readthedocs.projects.models.Project.checkout_path')
    def test_conda_with_cofig(self, checkout_path):
        base_path = tempfile.mkdtemp()
        checkout_path.return_value = base_path
        conda_file = 'environmemt.yml'
        full_conda_file = path.join(base_path, conda_file)
        with open(full_conda_file, 'w') as f:
            f.write('conda')
        create_config_file(
            {
                'conda': {
                    'file': conda_file,
                },
            },
            base_path=base_path,
        )
        config = load_yaml_config(self.version)
        self.assertTrue(config.conda is not None)
        self.assertEqual(config.conda.environment, conda_file)

    @mock.patch('readthedocs.projects.models.Project.checkout_path')
    def test_conda_without_cofig(self, checkout_path):
        base_path = tempfile.mkdtemp()
        checkout_path.return_value = base_path
        config = load_yaml_config(self.version)
        self.assertIsNone(config.conda)

    @mock.patch('readthedocs.projects.models.Project.checkout_path')
    def test_requirements_file_from_project_setting(self, checkout_path):
        base_path = tempfile.mkdtemp()
        checkout_path.return_value = base_path

        requirements_file = 'requirements.txt'
        self.project.requirements_file = requirements_file
        self.project.save()

        full_requirements_file = path.join(base_path, requirements_file)
        with open(full_requirements_file, 'w') as f:
            f.write('pip')

        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 1)
        self.assertEqual(
            config.python.install[0].requirements,
            requirements_file
        )

    @mock.patch('readthedocs.projects.models.Project.checkout_path')
    def test_requirements_file_from_yml(self, checkout_path):
        base_path = tempfile.mkdtemp()
        checkout_path.return_value = base_path

        self.project.requirements_file = 'no-existent-file.txt'
        self.project.save()

        requirements_file = 'requirements.txt'
        full_requirements_file = path.join(base_path, requirements_file)
        with open(full_requirements_file, 'w') as f:
            f.write('pip')
        create_config_file(
            {
                'requirements_file': requirements_file,
            },
            base_path=base_path,
        )
        config = load_yaml_config(self.version)
        self.assertEqual(len(config.python.install), 1)
        self.assertEqual(
            config.python.install[0].requirements,
            requirements_file
        )
