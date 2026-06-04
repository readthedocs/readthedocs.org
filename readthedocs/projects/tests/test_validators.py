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
def test_validate_translation_language_for_main_project():
    project = get(Project, slug="project", language="es")
    get(
        Project,
        slug="project-en",
        language="en",
        main_language_project=project,
    )

    with pytest.raises(ValidationError):
        validators.validate_translation_language(project=project, language="en")


@pytest.mark.django_db
def test_validate_translation_language_for_main_project_language():
    main_project = get(Project, slug="project", language="es")
    translation = get(
        Project,
        slug="project-en",
        language="en",
        main_language_project=main_project,
    )

    with pytest.raises(ValidationError):
        validators.validate_translation_language(project=translation, language="es")


@pytest.mark.django_db
def test_validate_translation_language_for_sibling_translation():
    main_project = get(Project, slug="project", language="es")
    get(
        Project,
        slug="project-en",
        language="en",
        main_language_project=main_project,
    )
    translation = get(
        Project,
        slug="project-br",
        language="pt-br",
        main_language_project=main_project,
    )

    with pytest.raises(ValidationError):
        validators.validate_translation_language(project=translation, language="en")


@pytest.mark.django_db
def test_validate_translation_language_allows_current_language():
    main_project = get(Project, slug="project", language="es")
    translation = get(
        Project,
        slug="project-en",
        language="en",
        main_language_project=main_project,
    )

    language = validators.validate_translation_language(
        project=translation, language="en"
    )
    assert language == "en"
