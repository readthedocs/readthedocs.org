"""Validations for the RTD configuration file."""

import os

from .exceptions import ConfigValidationError


def validate_list(value):
    """Check if ``value`` is an iterable."""
    if isinstance(value, (dict, str)):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_LIST,
            format_values={
                "value": value,
            },
        )
    if not hasattr(value, "__iter__"):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_LIST,
            format_values={
                "value": value,
            },
        )
    return list(value)


def validate_dict(value):
    """Check if ``value`` is a dictionary."""
    if not isinstance(value, dict):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_DICT,
            format_values={
                "value": value,
            },
        )


def validate_choice(value, choices):
    """Check that ``value`` is in ``choices``."""
    choices = validate_list(choices)
    if value not in choices:
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_CHOICE,
            format_values={
                "value": value,
                "choices": ", ".join(map(str, choices)),
            },
        )
    return value


def validate_bool(value):
    """Check that ``value`` is an boolean value."""
    if value not in (0, 1, False, True):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_BOOL,
            format_values={
                "value": value,
            },
        )
    return bool(value)


def validate_path(value, base_path):
    """Check that ``value`` is a valid path name and normamlize it."""
    string_value = validate_string(value)
    if not string_value:
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_PATH,
            format_values={
                "value": value,
            },
        )
    full_path = os.path.join(base_path, string_value)
    rel_path = os.path.relpath(full_path, base_path)
    return rel_path


def validate_path_pattern(value):
    """
    Normalize and validates a path pattern.

    - Normalizes the path stripping multiple ``/``.
    - Expands relative paths.
    - Checks the final path is relative to the root of the site ``/``.
    """
    path = validate_string(value)
    # Start the path with ``/`` to interpret the path as absolute to ``/``.
    path = "/" + path.lstrip("/")
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_PATH_PATTERN,
            format_values={
                "value": value,
            },
        )
    # Remove ``/`` from the path once is validated.
    path = path.lstrip("/")
    if not path:
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_PATH_PATTERN,
            format_values={
                "value": value,
            },
        )
    return path


def validate_string(value):
    """Check that ``value`` is a string type."""
    if not isinstance(value, str):
        raise ConfigValidationError(
            message_id=ConfigValidationError.INVALID_STRING,
            format_values={
                "value": value,
            },
        )
    return str(value)
