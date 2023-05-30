import tempfile
from os import path
from unittest import mock

import yaml
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.models import Version
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.projects.models import Project


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
