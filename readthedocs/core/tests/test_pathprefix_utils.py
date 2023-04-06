import pytest
from django.forms import ValidationError
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.core.utils.pathprefix import (
    validate_custom_prefix,
    validate_custom_subproject_prefix,
)
from readthedocs.projects.models import Project


class TestURLPatternsUtils(TestCase):
    def setUp(self):
        self.project = get(Project, slug="project")
        self.translation = get(
            Project,
            slug="translation",
            language="es",
            main_language_project=self.project,
        )
        self.subproject = get(Project, slug="subproject")
        self.subproject_translation = get(
            Project,
            slug="subproject-translation",
            language="es",
            main_language_project=self.subproject,
        )
        self.project.add_subproject(self.subproject)

    def test_validate_urlpattern(self):
        pattern = "/prefix/"
        self.assertEqual(validate_custom_prefix(self.project, pattern), "/prefix/")

        pattern = "prefix/"
        self.assertEqual(validate_custom_prefix(self.project, pattern), "/prefix/")

        pattern = "/prefix"
        self.assertEqual(validate_custom_prefix(self.project, pattern), "/prefix/")

        pattern = "//prefix//"
        self.assertEqual(validate_custom_prefix(self.project, pattern), "/prefix/")

        pattern = "/"
        self.assertEqual(validate_custom_prefix(self.project, pattern), "/")

    def test_validate_urlpattern_translation(self):
        with pytest.raises(ValidationError) as excinfo:
            pattern = "/prefix/"
            validate_custom_prefix(self.translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/prefix/"
            validate_custom_prefix(self.subproject_translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

    def test_validate_urlpattern_subproject(self):
        pattern = "/projects/"
        self.assertEqual(
            validate_custom_subproject_prefix(self.project, pattern), "/projects/"
        )

        pattern = "projects/"
        self.assertEqual(
            validate_custom_subproject_prefix(self.project, pattern), "/projects/"
        )

        pattern = "/projects"
        self.assertEqual(
            validate_custom_subproject_prefix(self.project, pattern), "/projects/"
        )

        pattern = "//projects//"
        self.assertEqual(
            validate_custom_subproject_prefix(self.project, pattern), "/projects/"
        )

        pattern = "/"
        self.assertEqual(validate_custom_subproject_prefix(self.project, pattern), "/")

    def test_validate_urlpattern_subproject_no_superproject(self):
        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/"
            validate_custom_subproject_prefix(self.subproject, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/"
            validate_custom_subproject_prefix(self.subproject_translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")
