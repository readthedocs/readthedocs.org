"""Validations for the RTD configuration file."""

import os


INVALID_BOOL = 'invalid-bool'
INVALID_CHOICE = 'invalid-choice'
INVALID_LIST = 'invalid-list'
INVALID_DICT = 'invalid-dictionary'
INVALID_PATH = 'invalid-path'
INVALID_STRING = 'invalid-string'
VALUE_NOT_FOUND = 'value-not-found'


class ValidationError(Exception):

    """Base error for validations."""

    messages = {
        INVALID_BOOL: 'expected one of (0, 1, true, false), got {value}',
        INVALID_CHOICE: 'expected one of ({choices}), got {value}',
        INVALID_DICT: '{value} is not a dictionary',
        INVALID_PATH: 'path {value} does not exist',
        INVALID_STRING: 'expected string',
        INVALID_LIST: 'expected list',
        VALUE_NOT_FOUND: '{value} not found',
    }

    def __init__(self, value, code, format_kwargs=None):
        self.value = value
        self.code = code
        defaults = {
            'value': value,
        }
        if format_kwargs is not None:
            defaults.update(format_kwargs)
        message = self.messages[code].format(**defaults)
        super().__init__(message)


def validate_list(value):
    """Check if ``value`` is an iterable."""
    if isinstance(value, (dict, str)):
        raise ValidationError(value, INVALID_LIST)
    if not hasattr(value, '__iter__'):
        raise ValidationError(value, INVALID_LIST)
    return list(value)


def validate_dict(value):
    """Check if ``value`` is a dictionary."""
    if not isinstance(value, dict):
        raise ValidationError(value, INVALID_DICT)


def validate_choice(value, choices):
    """Check that ``value`` is in ``choices``."""
    choices = validate_list(choices)
    if value not in choices:
        raise ValidationError(
            value,
            INVALID_CHOICE,
            {
                'choices': ', '.join(map(str, choices)),
            },
        )
    return value


def validate_bool(value):
    """Check that ``value`` is an boolean value."""
    if value not in (0, 1, False, True):
        raise ValidationError(value, INVALID_BOOL)
    return bool(value)


def validate_path(value, base_path):
    """Check that ``value`` is a valid path name and normamlize it."""
    string_value = validate_string(value)
    if not string_value:
        raise ValidationError(value, INVALID_PATH)
    full_path = os.path.join(base_path, string_value)
    rel_path = os.path.relpath(full_path, base_path)
    return rel_path


def validate_string(value):
    """Check that ``value`` is a string type."""
    if not isinstance(value, str):
        raise ValidationError(value, INVALID_STRING)
    return str(value)
