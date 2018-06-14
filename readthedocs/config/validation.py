import os
from six import string_types, text_type


INVALID_BOOL = 'invalid-bool'
INVALID_CHOICE = 'invalid-choice'
INVALID_LIST = 'invalid-list'
INVALID_DIRECTORY = 'invalid-directory'
INVALID_FILE = 'invalid-file'
INVALID_PATH = 'invalid-path'
INVALID_STRING = 'invalid-string'


class ValidationError(Exception):
    messages = {
        INVALID_BOOL: 'expected one of (0, 1, true, false), got {value}',
        INVALID_CHOICE: 'expected one of ({choices}), got {value}',
        INVALID_DIRECTORY: '{value} is not a directory',
        INVALID_FILE: '{value} is not a file',
        INVALID_PATH: 'path {value} does not exist',
        INVALID_STRING: 'expected string',
        INVALID_LIST: 'expected list',
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
        super(ValidationError, self).__init__(message)


def validate_list(value):
    if isinstance(value, str):
        raise ValidationError(value, INVALID_LIST)
    if not hasattr(value, '__iter__'):
        raise ValidationError(value, INVALID_LIST)
    return list(value)


def validate_choice(value, choices):
    choices = validate_list(choices)
    if value not in choices:
        raise ValidationError(value, INVALID_CHOICE, {
            'choices': ', '.join(map(str, choices))
        })
    return value


def validate_bool(value):
    if value not in (0, 1, False, True):
        raise ValidationError(value, INVALID_BOOL)
    return bool(value)


def validate_directory(value, base_path):
    path = validate_path(value, base_path)
    if not os.path.isdir(path):
        raise ValidationError(value, INVALID_DIRECTORY)
    return path


def validate_file(value, base_path):
    path = validate_path(value, base_path)
    if not os.path.isfile(path):
        raise ValidationError(value, INVALID_FILE)
    return path


def validate_path(value, base_path):
    string_value = validate_string(value)
    pathed_value = os.path.join(base_path, string_value)
    final_value = os.path.abspath(pathed_value)
    if not os.path.exists(final_value):
        raise ValidationError(value, INVALID_PATH)
    return final_value


def validate_string(value):
    if not isinstance(value, string_types):
        raise ValidationError(value, INVALID_STRING)
    return text_type(value)
