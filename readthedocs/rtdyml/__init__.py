"""Validator for the RTD configuration file."""

from os import path

import six

import yamale
from yamale.validators import DefaultValidators, Validator

V2_SCHEMA = path.join(
    path.dirname(__file__),
    '../rtd_tests/fixtures/spec/v2/schema.yml'
)


class PathValidator(Validator):

    """
    Path validator

    Checks if the given value is a string and a existing
    file.
    """

    tag = 'path'
    constraints = []
    configuration_file = '.'

    def _is_valid(self, value):
        if isinstance(value, six.string_types):
            file_ = path.join(
                path.dirname(self.configuration_file),
                value
            )
            return path.exists(file_)
        return False


class BuildConfig(object):

    """Wrapper object to validate to configuration file."""

    def __init__(self, configuration_file):
        self.configuration_file = configuration_file
        self.data = yamale.make_data(self.configuration_file)
        self.schema = yamale.make_schema(
            V2_SCHEMA,
            validators=self._get_validators()
        )

    def _get_validators(self):
        validators = DefaultValidators.copy()
        PathValidator.configuration_file = self.configuration_file
        validators[PathValidator.tag] = PathValidator
        return validators

    def validate(self):
        """Validate the current configuration file."""
        return yamale.validate(self.schema, self.data)
