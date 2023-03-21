import pytest
from django.core.exceptions import ValidationError

from readthedocs.projects import validators


def test_repository_path_validator():
    validator = validators.validate_repository_path(
        valid_filenames=[".readthedocs.yaml"]
    )

    # Invalid stuff
    with pytest.raises(ValidationError):
        validator("/absolute_path")

    with pytest.raises(ValidationError):
        validator("directory/")

    with pytest.raises(ValidationError):
        validator("../not_that")

    with pytest.raises(ValidationError):
        validator("../../../and_not_that/../")

    with pytest.raises(ValidationError):
        validator("'none_of_this'")

    with pytest.raises(ValidationError):
        validator('"and_none_of_this"')

    with pytest.raises(ValidationError):
        validator("nor_this.")

    with pytest.raises(ValidationError):
        validator(",you_probably_meant_to_use_a_dot")

    with pytest.raises(ValidationError):
        validator(".readthedocs.uml")

    # Valid stuff
    validator("this/is/okay/.readthedocs.yaml")
    validator("thiS/Is/oKay/.readthedocs.yaml")
    validator("this is okay/.readthedocs.yaml")
    validator("this_is_okay/.readthedocs.yaml")
    validator("this-is-okay/.readthedocs.yaml")
    validator(".readthedocs.yaml")

    validator = validators.validate_repository_path(
        valid_filenames=[".readthedocs.yaml", ".readthedocs.yml"]
    )
    validator(".readthedocs.yml")
