import tempfile
from unittest import mock
from unittest.mock import patch

import py
import pytest
from django.test import TestCase
from django.test.utils import override_settings

from readthedocs.config.tests.test_config import get_build_config
from readthedocs.doc_builder.backends.mkdocs import BaseMkdocs
from readthedocs.doc_builder.backends.sphinx import BaseSphinx
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.projects.exceptions import ProjectConfigurationError
from readthedocs.projects.exceptions import UserFileNotFound
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
            base_sphinx.show_conf()

        self.assertEqual(
            e.exception.message_id,
            ProjectConfigurationError.NOT_FOUND,
        )

    @patch("readthedocs.doc_builder.backends.sphinx.BaseSphinx.docs_dir")
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
                base_sphinx.show_conf()


@override_settings(PRODUCTION_DOMAIN="readthedocs.org")
class MkDocsBuilderTest(TestCase):
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

    @patch("readthedocs.doc_builder.backends.mkdocs.BaseMkdocs.run")
    @patch("readthedocs.projects.models.Project.checkout_path")
    @patch("readthedocs.doc_builder.python_environments.load_yaml_config")
    def test_project_without_mkdocs_yml(
        self,
        load_yaml_config,
        checkout_path,
        _,
    ):
        """
        Test for a project with a missing ``mkdocs.yml`` file.

        When ``mkdocs.configuration`` points to a file that doesn't exist,
        a ``UserFileNotFound`` error should be raised.
        """
        tmp_dir = tempfile.mkdtemp()
        checkout_path.return_value = tmp_dir
        python_env = Virtualenv(
            version=self.version,
            build_env=self.build_env,
            config=get_build_config(
                {"mkdocs": {"configuration": "mkdocs.yml"}},
                validate=True,
                source_file=f"{tmp_dir}/readthedocs.yml",
            ),
        )
        base_mkdocs = BaseMkdocs(
            build_env=self.build_env,
            python_env=python_env,
        )
        with self.assertRaises(UserFileNotFound) as e:
            base_mkdocs.show_conf()

        self.assertEqual(
            e.exception.message_id,
            UserFileNotFound.FILE_NOT_FOUND,
        )
        self.assertEqual(
            e.exception.format_values.get("filename"),
            "mkdocs.yml",
        )
