import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.projects.models import Feature, Project


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
        self.project.custom_prefix = "/prefix/"
        self.project.clean()
        self.assertEqual(self.project.custom_prefix, "/prefix/")

        self.project.custom_prefix = "prefix/"
        self.project.clean()
        self.assertEqual(self.project.custom_prefix, "/prefix/")

        self.project.custom_prefix = "/prefix"
        self.project.clean()
        self.assertEqual(self.project.custom_prefix, "/prefix/")

        self.project.custom_prefix = "//prefix//"
        self.project.clean()
        self.assertEqual(self.project.custom_prefix, "/prefix/")

        self.project.custom_prefix = "/"
        self.project.clean()
        self.assertEqual(self.project.custom_prefix, "/")

    def test_validate_urlpattern_translation(self):
        with pytest.raises(ValidationError) as excinfo:
            self.translation.custom_prefix = "/prefix/"
            self.translation.clean()
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            self.subproject_translation.custom_prefix = "/prefix/"
            self.subproject_translation.clean()
        self.assertEqual(excinfo.value.code, "invalid_project")

    def test_validate_urlpattern_subproject(self):
        self.project.custom_subproject_prefix = "/projects/"
        self.project.clean()
        self.assertEqual(self.project.custom_subproject_prefix, "/projects/")

        self.project.custom_subproject_prefix = "projects/"
        self.project.clean()
        self.assertEqual(self.project.custom_subproject_prefix, "/projects/")

        self.project.custom_subproject_prefix = "/projects"
        self.project.clean()
        self.assertEqual(self.project.custom_subproject_prefix, "/projects/")

        self.project.custom_subproject_prefix = "//projects//"
        self.project.clean()
        self.assertEqual(self.project.custom_subproject_prefix, "/projects/")

        self.project.custom_subproject_prefix = "/"
        self.project.clean()
        self.assertEqual(self.project.custom_subproject_prefix, "/")

    def test_validate_urlpattern_subproject_no_superproject(self):
        with pytest.raises(ValidationError) as excinfo:
            self.subproject.custom_subproject_prefix = "/projects/"
            self.subproject.clean()
        self.assertEqual(excinfo.value.code, "invalid_project")

        with pytest.raises(ValidationError) as excinfo:
            self.subproject_translation.custom_subproject_prefix = "/projects/"
            self.subproject_translation.clean()
        self.assertEqual(excinfo.value.code, "invalid_project")

    def test_overlapping_prefixes(self):
        self.project.custom_prefix = "/projects/"
        self.project.custom_subproject_prefix = "/projects/es"

        with pytest.raises(ValidationError) as excinfo:
            self.project.clean()
        self.assertEqual(excinfo.value.code, "ambiguous_path")

        self.project.custom_prefix = None
        self.project.custom_subproject_prefix = "es"
        with pytest.raises(ValidationError) as excinfo:
            self.project.clean()
        self.assertEqual(excinfo.value.code, "ambiguous_path")

        self.project.custom_prefix = "/projects/foo"
        self.project.custom_subproject_prefix = "/projects/foo/es"

        with pytest.raises(ValidationError) as excinfo:
            self.project.clean()
        self.assertEqual(excinfo.value.code, "ambiguous_path")

        self.project.custom_prefix = "/projects/foo"
        self.project.custom_subproject_prefix = "/projects/foo/es/bar/"

        with pytest.raises(ValidationError) as excinfo:
            self.project.clean()
        self.assertEqual(excinfo.value.code, "ambiguous_path")

    def test_proxied_api_prefix(self):
        self.assertEqual(self.project.custom_prefix, None)
        self.assertEqual(self.project.proxied_api_url, "_/")
        self.assertEqual(self.project.proxied_api_host, "/_")
        self.assertEqual(self.project.proxied_api_prefix, None)

        self.project.custom_prefix = "/prefix/"
        self.project.save()

        self.assertEqual(self.project.proxied_api_url, "_/")
        self.assertEqual(self.project.proxied_api_host, "/_")
        self.assertEqual(self.project.proxied_api_prefix, None)

        get(
            Feature,
            projects=[self.project],
            feature_id=Feature.USE_PROXIED_APIS_WITH_PREFIX,
        )
        self.assertEqual(self.project.proxied_api_url, "prefix/_/")
        self.assertEqual(self.project.proxied_api_host, "/prefix/_")
        self.assertEqual(self.project.proxied_api_prefix, "/prefix/")
