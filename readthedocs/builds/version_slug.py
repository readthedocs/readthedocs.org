"""Contains logic for handling version slugs.

Handling slugs for versions is not too straightforward. We need to allow some
characters which are uncommon in usual slugs. They are dots and underscores.
Usually we want the slug to be the name of the tag or branch corresponding VCS
version. However we need to strip url-destroying characters like slashes.

So the syntax for version slugs should be:

* Start with a lowercase ascii char or a digit.
* All other characters must be lowercase ascii chars, digits or dots.

If uniqueness is not met for a slug in a project, we append a dash and a letter
starting with ``a``. We keep increasing that letter until we have a unique
slug. This is used since using numbers in tags is too common and appending
another number would be confusing.
"""

from __future__ import absolute_import

import math
import re
import string
from operator import truediv

from django.db import models
from django.utils.encoding import force_text
from builtins import range


# Regex breakdown:
#   [a-z0-9] -- start with alphanumeric value
#   [-._a-z0-9] -- allow dash, dot, underscore, digit, lowercase ascii
#   *? -- allow multiple of those, but be not greedy about the matching
#   (?: ... ) -- wrap everything so that the pattern cannot escape when used in
#                regexes.
VERSION_SLUG_REGEX = '(?:[a-z0-9A-Z][-._a-z0-9A-Z]*?)'


class VersionSlugField(models.CharField):

    """Inspired by ``django_extensions.db.fields.AutoSlugField``."""

    invalid_chars_re = re.compile('[^-._a-z0-9]')
    leading_punctuation_re = re.compile('^[-._]+')
    placeholder = '-'
    fallback_slug = 'unknown'
    test_pattern = re.compile('^{pattern}$'.format(pattern=VERSION_SLUG_REGEX))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('db_index', True)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            raise ValueError("missing 'populate_from' argument")
        else:
            self._populate_from = populate_from
        super(VersionSlugField, self).__init__(*args, **kwargs)

    def get_queryset(self, model_cls, slug_field):
        # pylint: disable=protected-access
        for field, model in model_cls._meta.get_fields_with_model():
            if model and field == slug_field:
                return model._default_manager.all()
        return model_cls._default_manager.all()

    def slugify(self, content):
        if not content:
            return ''

        slugified = content.lower()
        slugified = self.invalid_chars_re.sub(self.placeholder, slugified)
        slugified = self.leading_punctuation_re.sub('', slugified)

        if not slugified:
            return self.fallback_slug
        return slugified

    def uniquifying_suffix(self, iteration):
        """
        Create a unique suffix.

        This creates a suffix based on the number given as ``iteration``. It
        will return a value encoded as lowercase ascii letter. So we have an
        alphabet of 26 letters. The returned suffix will be for example ``_yh``
        where ``yh`` is the encoding of ``iteration``. The length of it will be
        ``math.log(iteration, 26)``.

        Examples::

            uniquifying_suffix(0) == '_a'
            uniquifying_suffix(25) == '_z'
            uniquifying_suffix(26) == '_ba'
            uniquifying_suffix(52) == '_ca'
        """
        alphabet = string.ascii_lowercase
        length = len(alphabet)
        if iteration == 0:
            power = 0
        else:
            power = int(math.log(iteration, length))
        current = iteration
        suffix = ''
        for exp in reversed(list(range(0, power + 1))):
            digit = int(truediv(current, length ** exp))
            suffix += alphabet[digit]
            current = current % length ** exp
        return '_{suffix}'.format(suffix=suffix)

    def create_slug(self, model_instance):
        """Generate a unique slug for a model instance."""
        # pylint: disable=protected-access

        # get fields to populate from and slug field to set
        slug_field = model_instance._meta.get_field(self.attname)

        slug = self.slugify(getattr(model_instance, self._populate_from))
        count = 0

        # strip slug depending on max_length attribute of the slug field
        # and clean-up
        slug_len = slug_field.max_length
        if slug_len:
            slug = slug[:slug_len]
        original_slug = slug

        # exclude the current model instance from the queryset used in finding
        # the next valid slug
        queryset = self.get_queryset(model_instance.__class__, slug_field)
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to implement any unique_together constraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)
        kwargs[self.attname] = slug

        # increases the number while searching for the next valid slug
        # depending on the given slug, clean-up
        while not slug or queryset.filter(**kwargs):
            slug = original_slug
            end = self.uniquifying_suffix(count)
            end_len = len(end)
            if slug_len and len(slug) + end_len > slug_len:
                slug = slug[:slug_len - end_len]
            slug = slug + end
            kwargs[self.attname] = slug
            count += 1

        assert self.test_pattern.match(slug), (
            'Invalid generated slug: {slug}'.format(slug=slug))
        return slug

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        # We only create a new slug if none was set yet.
        if not value and add:
            value = force_text(self.create_slug(model_instance))
            setattr(model_instance, self.attname, value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super(VersionSlugField, self).deconstruct()
        kwargs['populate_from'] = self._populate_from
        return name, path, args, kwargs
