import pytest
from django.core.exceptions import ValidationError

from readthedocs.projects import validators


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
