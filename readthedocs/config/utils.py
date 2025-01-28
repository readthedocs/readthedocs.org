"""Shared functions for the config module."""


def list_to_dict(list_):
    """Transform a list to a dictionary with its indices as keys."""
    dict_ = {str(i): element for i, element in enumerate(list_)}
    return dict_
