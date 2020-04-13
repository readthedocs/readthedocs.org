"""Shared functions for the config module."""

import yaml


def to_dict(value):
    """Recursively transform a class from `config.models` to a dict."""
    if hasattr(value, 'as_dict'):
        return value.as_dict()
    if isinstance(value, list):
        return [
            to_dict(v)
            for v in value
        ]
    if isinstance(value, dict):
        return {
            k: to_dict(v)
            for k, v in value.items()
        }
    return value


def list_to_dict(list_):
    """Transform a list to a dictionary with its indices as keys."""
    dict_ = {
        str(i): element
        for i, element in enumerate(list_)
    }
    return dict_


class SafeLoaderIgnoreUnknown(yaml.SafeLoader):

    """
    YAML loader to ignore unknown tags.

    Borrowed from https://stackoverflow.com/a/57121993
    """
    def ignore_unknown(self, node):
        return None


SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)


def yaml_load_safely(content):
    """
    Uses ``SafeLoaderIgnoreUnknown`` loader to skip unknown tags.

    When a YAML contains ``!!python/name:int`` it will complete ignore it an return ``None`` for those fields
    instead of failing. We need this to avoid executing random code, but still support these YAML files.
    """
    return yaml.load(content, Loader=SafeLoaderIgnoreUnknown)
