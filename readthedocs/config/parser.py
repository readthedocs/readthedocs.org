# -*- coding: utf-8 -*-
"""YAML parser for the RTD configuration file."""

from __future__ import division, print_function, unicode_literals

import yaml

__all__ = ('parse', 'ParseError')


class ParseError(Exception):

    """Parser related errors."""

    pass


def parse(stream):
    """
    Take file-like object and return a list of project configurations.

    The files need be valid YAML and only contain mappings as documents.
    Everything else raises a ``ParseError``.
    """
    try:
        configs = list(yaml.safe_load_all(stream))
    except yaml.YAMLError as error:
        raise ParseError('YAML: {message}'.format(message=error))
    if not configs:
        raise ParseError('Empty config')
    for config in configs:
        if not isinstance(config, dict):
            raise ParseError('Expected mapping')
    return configs
