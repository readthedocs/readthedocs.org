# -*- coding: utf-8 -*-

"""
Contains logic for handling version slugs.

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

import math
import re
import string
from operator import truediv

from django.db import models
from django.utils.encoding import force_text
from slugify import slugify


def get_fields_with_model(cls):
    """
    Replace deprecated function of the same name in Model._meta.

    This replaces deprecated function (as of Django 1.10) in Model._meta as
    prescrived in the Django docs.
    https://docs.djangoproject.com/en/1.11/ref/models/meta/#migrating-from-the-old-api
    """
    return [(f, f.model if f.model != cls else None)
            for f in cls._meta.get_fields()
            if not f.is_relation or f.one_to_one or
            (f.many_to_one and f.related_model)]


# Regex breakdown:
#   [a-z0-9] -- start with alphanumeric value
#   [-._a-z0-9] -- allow dash, dot, underscore, digit, lowercase ascii
#   *? -- allow multiple of those, but be not greedy about the matching
#   (?: ... ) -- wrap everything so that the pattern cannot escape when used in
#                regexes.
VERSION_SLUG_REGEX = '(?:[a-z0-9A-Z][-._a-z0-9A-Z]*?)'


class VersionSlugField(models.CharField):

    """
    Inspired by ``django_extensions.db.fields.AutoSlugField``.

    Uses ``unicode-slugify`` to generate the slug.
    """

    ok_chars = '-._'  # dash, dot, underscore
    test_pattern = re.compile('^{pattern}$'.format(pattern=VERSION_SLUG_REGEX))
    fallback_slug = 'unknown'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('db_index', True)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            raise ValueError("missing 'populate_from' argument")
        else:
            self._populate_from = populate_from
        super().__init__(*args, **kwargs)

    def get_queryset(self, model_cls, slug_field):
        # pylint: disable=protected-access
        for field, model in get_fields_with_model(model_cls):
            if model and field == slug_field:
                return model._default_manager.all()
        return model_cls._default_manager.all()

    def _normalize(self, content):
        """
        Normalize some invalid characters to become a dash (``-``).

        For example, ``release/1.0`` will become ``release-1.0``.
        """
        return re.sub('[/%!?]', '-', content)

    def slugify(self, content):
        """
        Make ``content`` a valid slug.

        It uses ``unicode-slugify`` behind the scenes which works properly with
        Unicode characters.
        """
        if not content:
            return ''

        normalized = self._normalize(content)
        slugified = slugify(
            normalized,
            only_ascii=True,
            spaces=False,
            lower=True,
            ok=self.ok_chars,
            space_replacement='-',
        )

        # Remove first character wile it's an invalid character for the
        # beginning of the slug
        slugified = slugified.lstrip(self.ok_chars)

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
        while not slug or queryset.filter(**kwargs).exists():
            slug = original_slug
            end = self.uniquifying_suffix(count)
            end_len = len(end)
            if slug_len and len(slug) + end_len > slug_len:
                slug = slug[:slug_len - end_len]
            slug = slug + end
            kwargs[self.attname] = slug
            count += 1

        assert self.test_pattern.match(slug), (
            'Invalid generated slug: {slug}'.format(slug=slug)
        )
        return slug

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        # We only create a new slug if none was set yet.
        if not value and add:
            value = force_text(self.create_slug(model_instance))
            setattr(model_instance, self.attname, value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['populate_from'] = self._populate_from
        return name, path, args, kwargs
