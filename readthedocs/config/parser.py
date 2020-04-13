# -*- coding: utf-8 -*-

"""YAML parser for the RTD configuration file."""

import yaml

from .utils import yaml_load_safely

__all__ = ('parse', 'ParseError')


class ParseError(Exception):

    """Parser related errors."""


def parse(stream):
    """
    Take file-like object and return a project configuration.

    The file need be valid YAML and only contain mappings as document.
    Everything else raises a ``ParseError``.
    """
    try:
        config = yaml_load_safely(stream)
    except yaml.YAMLError as error:
        raise ParseError('YAML: {message}'.format(message=error))
    if not isinstance(config, dict):
        raise ParseError('Expected mapping')
    if not config:
        raise ParseError('Empty config')
    return config
