from django.test import TestCase

from django_dynamic_fixture import get
from readthedocs_build.config import BuildConfig

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.doc_builder.config import ConfigWrapper


def get_build_config(config, env_config=None, source_file='readthedocs.yml',
                     source_position=0):
    config['name'] = 'test'
    config['type'] = 'sphinx'
    ret_config = BuildConfig(
        {'output_base': ''},
        config,
        source_file=source_file,
        source_position=source_position)
    ret_config.validate()
    return ret_config


class ConfigWrapperTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='test', python_interpreter='python',
                           install_project=False, requirements_file='requirements/pip.txt')
        self.version = get(Version, project=self.project, slug='foobar')

    def test_python_version(self):
        yaml_config = get_build_config({'python': {'version': 3}})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.python_version, 3)

        yaml_config = get_build_config({})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.python_version, 2)

    def test_python_interpreter(self):
        yaml_config = get_build_config({'python': {'version': 3}})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.python_interpreter, 'python3')

        yaml_config = get_build_config({})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.python_interpreter, 'python')

    def test_install_project(self):
        yaml_config = get_build_config({'python': {'setup_py_install': True}})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.install_project, True)

        yaml_config = get_build_config({})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.install_project, False)

    def test_conda(self):
        yaml_config = get_build_config({'conda': {'file': '.travis.yml'}})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.use_conda, True)
        self.assertTrue(config.conda_file[-11:] == '.travis.yml')

        yaml_config = get_build_config({})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.use_conda, False)
        self.assertEqual(config.conda_file, None)

    def test_requirements_file(self):
        yaml_config = get_build_config({'requirements_file': 'requirements/deploy.txt'})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.requirements_file, 'requirements/deploy.txt')

        yaml_config = get_build_config({})
        config = ConfigWrapper(version=self.version, yaml_config=yaml_config)
        self.assertEqual(config.requirements_file, 'requirements/pip.txt')
