"""Customizations to Django Taggit"""
from django.utils.text import slugify
from taggit.utils import _parse_tags


def rtd_parse_tags(tag_string):
    """
    Parses a string into its tags

    - Lowercases all tags
    - Slugifies tags

    :see: https://django-taggit.readthedocs.io/page/custom_tagging.html
    :param tag_string: a delimited string of tags
    :return: a sorted list of tag strings
    """
    if tag_string:
        tag_string = tag_string.lower()

    return [slugify(tag) for tag in _parse_tags(tag_string)]
