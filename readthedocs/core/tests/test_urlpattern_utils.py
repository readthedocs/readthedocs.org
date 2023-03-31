import pytest
from django.forms import ValidationError
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.core.utils.urlpattern import (
    validate_urlpattern,
    validate_urlpattern_subproject,
    wrap_urlpattern,
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
        pattern = "/{language}(/({version}(/{filename})?)?)?"
        validate_urlpattern(self.project, pattern)

        with pytest.raises(ValidationError) as excinfo:
            pattern = "{language}(/({version}(/{filename})?)?)?"
            validate_urlpattern(self.project, pattern)
        self.assertEqual(excinfo.value.code, "missing_leading_slash")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({version_slug}(/{filename})?)?)?"
            validate_urlpattern(self.project, pattern)
        self.assertEqual(excinfo.value.code, "missing_replacement_field")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({version}{extra}(/{filename})?)?)?"
            validate_urlpattern(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_replacement_field")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({version}(/{filename})?)?)?+"
            validate_urlpattern(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_regex")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({filename}(/{version})?)?)?"
            validate_urlpattern(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_filename_position")

    def test_validate_urlpattern_translation(self):
        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({version}(/{filename})?)?)?"
            validate_urlpattern(self.translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/{language}(/({version}(/{filename})?)?)?"
            validate_urlpattern(self.subproject_translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

    def test_validate_urlpattern_subproject(self):
        pattern = "/projects/{subproject}(/{filename})?"
        validate_urlpattern_subproject(self.project, pattern)

        with pytest.raises(ValidationError) as excinfo:
            pattern = "projects/{subproject}(/{filename})?"
            validate_urlpattern_subproject(self.project, pattern)
        self.assertEqual(excinfo.value.code, "missing_leading_slash")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{subproject_alias}(/{filename})?"
            validate_urlpattern_subproject(self.project, pattern)
        self.assertEqual(excinfo.value.code, "missing_replacement_field")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{subproject}{extra}(/{filename})?"
            validate_urlpattern_subproject(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_replacement_field")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{subproject}(/{filename})?+"
            validate_urlpattern_subproject(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_regex")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{filename}(/{subproject})?"
            validate_urlpattern_subproject(self.project, pattern)
        self.assertEqual(excinfo.value.code, "invalid_filename_position")

    def test_validate_urlpattern_subproject_no_superproject(self):
        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{subproject}(/{filename})?"
            validate_urlpattern_subproject(self.subproject, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            pattern = "/projects/{subproject}(/{filename})?"
            validate_urlpattern_subproject(self.subproject_translation, pattern)
        self.assertEqual(excinfo.value.code, "invalid_project")

    def test_wrap_urlpattern(self):
        patterns = [
            # URL patterns
            (
                "/{language}/{version}/{filename}",
                "/{language}(/({version}(/({filename})?)?)?)?",
            ),
            (
                "/prefix/{language}/{version}/{filename}",
                "/prefix/{language}(/({version}(/({filename})?)?)?)?",
            ),
            (
                "/custom/prefix/{language}/{version}/{filename}",
                "/custom/prefix/{language}(/({version}(/({filename})?)?)?)?",
            ),
            (
                "/{version}/{language}/{filename}",
                "/{version}(/({language}(/({filename})?)?)?)?",
            ),
            # Subproject URL pattern
            ("/{subproject}/{filename}", "/{subproject}(/({filename})?)?"),
            (
                "/custom/{subproject}/prefix/{filename}",
                "/custom/{subproject}/prefix(/({filename})?)?",
            ),
            ("/s/{subproject}/{filename}", "/s/{subproject}(/({filename})?)?"),
        ]
        for pattern, expected in patterns:
            self.assertEqual(wrap_urlpattern(pattern), expected)

    def test_wrap_urlpattern_single_version(self):
        patterns = [
            ("/{filename}", "/{filename}"),
            ("/custom-prefix/{filename}", "/custom-prefix(/({filename})?)?"),
        ]
        for pattern, expected in patterns:
            self.assertEqual(wrap_urlpattern(pattern, single_version=True), expected)
