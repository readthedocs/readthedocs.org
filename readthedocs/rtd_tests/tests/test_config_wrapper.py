from __future__ import absolute_import
import mock
from django.test import TestCase
from django_dynamic_fixture import get

import six

from readthedocs_build.config import BuildConfig, ProjectConfig, InvalidConfig
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.doc_builder.config import ConfigWrapper, load_yaml_config


def create_load(config=None):
    """Mock out the function of the build load function

    This will create a ProjectConfig list of BuildConfig objects and validate
    them. The default load function iterates over files and builds up a list of
    objects. Instead of mocking all of this, just mock the end result.
    """
    if config is None:
        config = {}

    def inner(path=None, env_config=None):
        env_config_defaults = {
            'output_base': '',
            'name': '1',
            'type': 'sphinx',
        }
        if env_config is not None:
            env_config_defaults.update(env_config)
        yaml_config = ProjectConfig([
            BuildConfig(env_config_defaults,
                        config,
                        source_file='readthedocs.yml',
                        source_position=0)
        ])
        yaml_config.validate()
        return yaml_config
    return inner


@mock.patch('readthedocs.doc_builder.config.load_config')
class LoadConfigTests(TestCase):

    def setUp(self):
        self.project = get(Project, main_language_project=None,
                           install_project=False, requirements_file='urls.py')
        self.version = get(Version, project=self.project)

    def test_python_supported_versions_default_image_1_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:1.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(load_config.call_count, 1)
        load_config.assert_has_calls([
            mock.call(path=mock.ANY, env_config={
                'python': {'supported_versions': [2, 2.7, 3, 3.4]},
                'type': 'sphinx',
                'output_base': '',
                'name': mock.ANY
            }),
        ])
        self.assertEqual(config.python_version, 2)

    def test_python_supported_versions_image_2_0(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(load_config.call_count, 1)
        load_config.assert_has_calls([
            mock.call(path=mock.ANY, env_config={
                'python': {'supported_versions': [2, 2.7, 3, 3.5]},
                'type': 'sphinx',
                'output_base': '',
                'name': mock.ANY
            }),
        ])
        self.assertEqual(config.python_version, 2)

    def test_python_supported_versions_image_latest(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:latest'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(load_config.call_count, 1)
        load_config.assert_has_calls([
            mock.call(path=mock.ANY, env_config={
                'python': {'supported_versions': [2, 2.7, 3, 3.3, 3.4, 3.5, 3.6]},
                'type': 'sphinx',
                'output_base': '',
                'name': mock.ANY
            }),
        ])
        self.assertEqual(config.python_version, 2)

    def test_python_default_version(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python_version, 2)
        self.assertEqual(config.python_interpreter, 'python2.7')

    def test_python_set_python_version_on_project(self, load_config):
        load_config.side_effect = create_load()
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.python_interpreter = 'python3'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python_version, 3)
        self.assertEqual(config.python_interpreter, 'python3.5')

    def test_python_set_python_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 3.5}
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        config = load_yaml_config(self.version)
        self.assertEqual(config.python_version, 3.5)
        self.assertEqual(config.python_interpreter, 'python3.5')

    def test_python_invalid_version_in_config(self, load_config):
        load_config.side_effect = create_load({
            'python': {'version': 2.6}
        })
        self.project.container_image = 'readthedocs/build:2.0'
        self.project.save()
        with self.assertRaises(InvalidConfig):
            config = load_yaml_config(self.version)

    def test_install_project(self, load_config):
        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.install_project, False)

        load_config.side_effect = create_load({
            'python': {'setup_py_install': True}
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.install_project, True)

    def test_extra_requirements(self, load_config):
        load_config.side_effect = create_load({
            'python': {
                'pip_install': True,
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.extra_requirements, ['tests', 'docs'])

        load_config.side_effect = create_load({
            'python': {
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.extra_requirements, [])

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.extra_requirements, [])

        load_config.side_effect = create_load({
            'python': {
                'setup_py_install': True,
                'extra_requirements': ['tests', 'docs']
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.extra_requirements, [])

    def test_conda(self, load_config):
        to_find = 'urls.py'
        load_config.side_effect = create_load({
            'conda': {
                'file': to_find
            }
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.use_conda, True)
        self.assertTrue(config.conda_file[-len(to_find):] == to_find)

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.use_conda, False)
        self.assertEqual(config.conda_file, None)

    def test_requirements_file(self, load_config):
        if six.PY3:
            import pytest
            pytest.xfail("test_requirements_file is known to fail on 3.6")

        requirements_file = 'wsgi.py' if six.PY2 else 'readthedocs/wsgi.py'
        load_config.side_effect = create_load({
            'requirements_file': requirements_file
        })
        config = load_yaml_config(self.version)
        self.assertEqual(config.requirements_file, requirements_file)

        load_config.side_effect = create_load()
        config = load_yaml_config(self.version)
        self.assertEqual(config.requirements_file, 'urls.py')
