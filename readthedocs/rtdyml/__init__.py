"""Validator for the RTD configuration file."""

from os import path

import six

import yamale
from yamale.validators import DefaultValidators, Validator

V2_SCHEMA = path.join(
    path.dirname(__file__),
    '../rtd_tests/fixtures/spec/v2/schema.yml'
)

ALL = 'all'

DEFAULT_VALUES = {
    'formats': [],
    'conda': None,
    'build': {
        'image': '2.0',
    },
    'python': {
        'version': '3.6',
        'requirements': None,
        'install': None,
        'extra_requirements': [],
        'system_packages': False,
    },
    'sphinx': {
        'configuration': None,
        'fail_on_warning': False,
    },
    'mkdocs': {
        'configuration': None,
        'fail_on_warning': False,
    },
    'submodules': {
        'include': [],
        'exclude': [],
        'recursive': False,
    },
    'redirects': None,
}


def flatten(dic, keep_key=False, position=None):
    """Returns a flattened dictionary from a dictionary of nested dictionaries."""
    child = {}

    for key, value in dic.items():
        if isinstance(key, six.string_types):
            key = key.replace('.', '_')
        if position:
            item_position = '{}.{}'.format(position, key)
        else:
            item_position = key

        if isinstance(value, dict):
            child.update(
                flatten(dic[key], keep_key, item_position)
            )
            if keep_key:
                child[item_position] = value
        else:
            child[item_position] = value

    return child


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
        self.defaults = flatten(DEFAULT_VALUES, keep_key=True)
        self.schema = yamale.make_schema(
            V2_SCHEMA,
            validators=self._get_validators()
        )

    def _get_validators(self):
        validators = DefaultValidators.copy()
        PathValidator.configuration_file = self.configuration_file
        validators[PathValidator.tag] = PathValidator
        return validators

    def check_constraints(self):
        """
        Check constraints between keys.

        Such as relations of uniquiness and set default values for those.
        """
        constraints = {
            'Documentation type': {
                'unique': ['sphinx', 'mkdocs'],
                'default': 'sphinx',
            },
            'Submodules': {
                'unique': ['submodules.include', 'submodules.exclude'],
                'default': 'submodules.include',
            }
        }

        for subject, constraint in constraints.items():
            present_keys = [
                key
                for key in constraint['unique']
                if key in self.data[0]
            ]
            default_key = constraint.get('default')
            if not present_keys and default_key:
                self.data[0][default_key] = self.defaults[default_key]
            elif len(present_keys) > 1:
                raise ValueError(
                    '{subject} can not have {keys} at the same time'.format(
                        subject=subject,
                        keys=constraint['unique'],
                    )
                )

    def set_defaults(self):
        """Set default values to the currently processed data."""
        for key, value in self.defaults.items():
            if key not in self.data[0]:
                self.data[0][key] = value

    def validate(self):
        """Validate the current configuration file."""
        self.check_constraints()
        self.set_defaults()
        return yamale.validate(self.schema, self.data)
