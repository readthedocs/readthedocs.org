"""Shared functions for the config module."""


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
