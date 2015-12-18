from django.test import TestCase

from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.doc_builder.config import ConfigWrapper


class GoldViewTests(TestCase):

    def setUp(self):
        self.project = get(Project, slug='test', python_interpreter='python3',
                           install_project=False, requirements_file='req_model.txt')
        self.version = get(Version, project=self.project, slug='foobar')

    def test_python_version(self):
        config = ConfigWrapper(version=self.version, yaml_config={'python': {'version': 2}})
        self.assertEqual(config.python_version, 2)

        config = ConfigWrapper(version=self.version, yaml_config={})
        self.assertEqual(config.python_version, 3)

    def test_python_interpreter(self):
        config = ConfigWrapper(version=self.version, yaml_config={'python': {'version': 2}})
        self.assertEqual(config.python_interpreter, 'python')

        config = ConfigWrapper(version=self.version, yaml_config={})
        self.assertEqual(config.python_interpreter, 'python3')

    def test_install_project(self):
        config = ConfigWrapper(version=self.version, yaml_config={'install_project': True})
        self.assertEqual(config.install_project, True)

        config = ConfigWrapper(version=self.version, yaml_config={})
        self.assertEqual(config.install_project, False)

    def test_conda(self):
        config = ConfigWrapper(version=self.version, yaml_config={'conda': {'file': 'env.yml'}})
        self.assertEqual(config.use_conda, True)
        self.assertEqual(config.conda_file, 'env.yml')

        config = ConfigWrapper(version=self.version, yaml_config={})
        self.assertEqual(config.use_conda, False)
        self.assertEqual(config.conda_file, None)

    def test_requirements_file(self):
        config = ConfigWrapper(version=self.version, yaml_config={'requirements_file': 'req_yaml.txt'})
        self.assertEqual(config.requirements_file, 'req_yaml.txt')

        config = ConfigWrapper(version=self.version, yaml_config={})
        self.assertEqual(config.requirements_file, 'req_model.txt')
