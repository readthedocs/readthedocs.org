import os
import tempfile
from unittest import mock
from unittest.mock import patch

import py
import pytest
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.config.tests.test_config import get_build_config
from readthedocs.doc_builder.backends.sphinx import BaseSphinx
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.models import Project


@override_settings(PRODUCTION_DOMAIN="readthedocs.org")
class SphinxBuilderTest(TestCase):
    fixtures = ["test_data", "eric"]

    def setUp(self):
        self.project = Project.objects.get(slug="pip")
        self.version = self.project.versions.first()

        self.build_env = mock.MagicMock()
        self.build_env.project = self.project
        self.build_env.version = self.version
        self.build_env.build = {
            "id": 123,
        }
        self.build_env.api_client = mock.MagicMock()

        BaseSphinx.type = "base"
        BaseSphinx.sphinx_build_dir = tempfile.mkdtemp()
        BaseSphinx.relative_output_dir = "_readthedocs/"

    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.docs_dir")
    @patch("readthedocs.projects.models.Project.checkout_path")
    @patch("readthedocs.doc_builder.python_environments.load_yaml_config")
    def test_conf_py_path(self, load_yaml_config, checkout_path, docs_dir):
        """
        Test the conf_py_path that is added to the conf.py file.

        This value is used from the theme and footer
        to build the ``View`` and ``Edit`` on link.
        """
        tmp_dir = tempfile.mkdtemp()
        checkout_path.return_value = tmp_dir
        docs_dir.return_value = tmp_dir
        python_env = Virtualenv(
            version=self.version,
            build_env=self.build_env,
            config=get_build_config({}, validate=True),
        )
        base_sphinx = BaseSphinx(
            build_env=self.build_env,
            python_env=python_env,
        )

        for value, expected in (("conf.py", "/"), ("docs/conf.py", "/docs/")):
            base_sphinx.config_file = os.path.join(
                tmp_dir,
                value,
            )
            params = base_sphinx.get_config_params()
            self.assertEqual(
                params["conf_py_path"],
                expected,
            )

    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.docs_dir")
    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.get_config_params")
    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.run")
    @patch("readthedocs.builds.models.Version.get_conf_py_path")
    @patch("readthedocs.projects.models.Project.checkout_path")
    @patch("readthedocs.doc_builder.python_environments.load_yaml_config")
    def test_project_without_conf_py(
        self,
        load_yaml_config,
        checkout_path,
        get_conf_py_path,
        _,
        get_config_params,
        docs_dir,
    ):
        """
        Test for a project without ``conf.py`` file.

        When this happen, the ``get_conf_py_path`` raises a
        ``ProjectConfigurationError`` which is captured by our own code.
        """
        tmp_dir = tempfile.mkdtemp()
        checkout_path.return_value = tmp_dir
        docs_dir.return_value = tmp_dir
        get_config_params.return_value = {}
        get_conf_py_path.side_effect = ProjectConfigurationError
        python_env = Virtualenv(
            version=self.version,
            build_env=self.build_env,
            config=get_build_config({}, validate=True),
        )
        base_sphinx = BaseSphinx(
            build_env=self.build_env,
            python_env=python_env,
        )
        with self.assertRaises(ProjectConfigurationError) as e:
            base_sphinx.append_conf()

        self.assertEqual(
            e.exception.message_id,
            ProjectConfigurationError.NOT_FOUND,
        )

    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.docs_dir")
    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.get_config_params")
    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.run")
    @patch("readthedocs.builds.models.Version.get_conf_py_path")
    @patch("readthedocs.projects.models.Project.checkout_path")
    @patch("readthedocs.doc_builder.python_environments.load_yaml_config")
    def test_multiple_conf_py(
        self,
        load_yaml_config,
        checkout_path,
        get_conf_py_path,
        _,
        get_config_params,
        docs_dir,
    ):
        """
        Test for a project with multiple ``conf.py`` files.

        An error should be raised to the user if we can't
        guess the correct conf.py file.
        """

        tmp_docs_dir = py.path.local(tempfile.mkdtemp())
        tmp_docs_dir.join("conf.py").write("")
        tmp_docs_dir.join("test").mkdir().join("conf.py").write("")
        docs_dir.return_value = str(tmp_docs_dir)
        checkout_path.return_value = str(tmp_docs_dir)
        get_config_params.return_value = {}
        get_conf_py_path.side_effect = ProjectConfigurationError
        python_env = Virtualenv(
            version=self.version,
            build_env=self.build_env,
            config=get_build_config({}, validate=True),
        )
        base_sphinx = BaseSphinx(
            build_env=self.build_env,
            python_env=python_env,
        )
        with pytest.raises(ProjectConfigurationError):
            with override_settings(DOCROOT=tmp_docs_dir):
                base_sphinx.append_conf()
