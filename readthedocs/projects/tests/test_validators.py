import pytest
from django.core.exceptions import ValidationError
from django_dynamic_fixture import get

from readthedocs.projects import validators
from readthedocs.projects.models import Project


def test_repository_path_validator():
    # Invalid stuff
    with pytest.raises(ValidationError):
        validators.validate_build_config_file("/absolute_path")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file("directory/")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file("../not_that")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file("../../../and_not_that/../")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file("'none_of_this'")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file('"and_none_of_this"')

    with pytest.raises(ValidationError):
        validators.validate_build_config_file("nor_this.")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file(",you_probably_meant_to_use_a_dot")

    with pytest.raises(ValidationError):
        validators.validate_build_config_file(".readthedocs.uml")

    # Valid stuff
    validators.validate_build_config_file("this/is/okay/.readthedocs.yaml")
    validators.validate_build_config_file("thiS/Is/oKay/.readthedocs.yaml")
    validators.validate_build_config_file("this is okay/.readthedocs.yaml")
    validators.validate_build_config_file("this_is_okay/.readthedocs.yaml")
    validators.validate_build_config_file("this-is-okay/.readthedocs.yaml")
    validators.validate_build_config_file(".readthedocs.yaml")


@pytest.mark.django_db
class TestValidateLanguage:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.main = get(Project, language="es", main_language_project=None)
        self.translation_en = get(Project, language="en", main_language_project=None)
        self.translation_br = get(Project, language="br", main_language_project=None)
        self.main.translations.add(self.translation_en)
        self.main.translations.add(self.translation_br)

    def test_unused_language_is_valid(self):
        assert validators.validate_language("fr", self.main) == "fr"

    def test_same_language_as_self_is_valid(self):
        # A project keeping its own language is fine.
        assert validators.validate_language("es", self.main) == "es"
        assert validators.validate_language("en", self.translation_en) == "en"

    def test_main_cant_use_translation_language(self):
        with pytest.raises(ValidationError) as excinfo:
            validators.validate_language("en", self.main)
        assert 'There is already a "en" translation' in str(excinfo.value)

    def test_translation_cant_use_main_language(self):
        with pytest.raises(ValidationError) as excinfo:
            validators.validate_language("es", self.translation_en)
        assert 'There is already a "es" translation' in str(excinfo.value)

    def test_translation_cant_use_sibling_language(self):
        with pytest.raises(ValidationError) as excinfo:
            validators.validate_language("br", self.translation_en)
        assert 'There is already a "br" translation' in str(excinfo.value)

    def test_project_without_translations_is_valid(self):
        project = get(Project, language="en", main_language_project=None)
        assert validators.validate_language("ru", project) == "ru"
