import pytest
from django.core.exceptions import ValidationError

from readthedocs.projects import validators


def test_repository_path_validator():

    # Invalid stuff
    with pytest.raises(ValidationError):
        validators.validate_repository_path("/absolute_path")

    with pytest.raises(ValidationError):
        validators.validate_repository_path("directory/")

    with pytest.raises(ValidationError):
        validators.validate_repository_path("spaces are too weird")

    with pytest.raises(ValidationError):
        validators.validate_repository_path("../not_that")

    with pytest.raises(ValidationError):
        validators.validate_repository_path("../../../and_not_that/../")

    with pytest.raises(ValidationError):
        validators.validate_repository_path("'none_of_this'")

    with pytest.raises(ValidationError):
        validators.validate_repository_path('"and_none_of_this"')

    with pytest.raises(ValidationError):
        validators.validate_repository_path("nor_this.")

    with pytest.raises(ValidationError):
        validators.validate_repository_path(",you_probably_meant_to_use_a_dot")

    # Valid stuff
    validators.validate_repository_path("møltilinguål_is_ok")
    validators.validate_repository_path("MixedCaseIsCoolToo")
    validators.validate_repository_path("this/is/valid")
    validators.validate_repository_path("this/is/valid.yaml")
    validators.validate_repository_path("this/is-also/valid.yaml")
    validators.validate_repository_path(".readthedocs.yaml")
