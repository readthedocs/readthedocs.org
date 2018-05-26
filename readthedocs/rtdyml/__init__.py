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
    Docstring
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

    def __init__(self, configuration_file):
        self.configuration_file = configuration_file
        self.data = yamale.make_data(self.configuration_file)
        self.schema = yamale.make_schema(
            V2_SCHEMA,
            validators=self.get_validators()
        )

    def get_validators(self):
        validators = DefaultValidators.copy()
        PathValidator.configuration_file = self.configuration_file
        validators[PathValidator.tag] = PathValidator
        return validators

    def validate(self):
        return yamale.validate(self.schema, self.data)
