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

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from slugify import slugify as unicode_slugify


class VersionSlugField(models.CharField):
    """Just for backwards compatibility with old migrations."""


# Regex breakdown:
#   [a-z0-9] -- start with alphanumeric value
#   [-._a-z0-9] -- allow dash, dot, underscore, digit, lowercase ascii
#   *? -- allow multiple of those, but be not greedy about the matching
#   (?: ... ) -- wrap everything so that the pattern cannot escape when used in
#                regexes.
VERSION_SLUG_REGEX = "(?:[a-z0-9A-Z][-._a-z0-9A-Z]*?)"


def validate_version_slug(*, project, pk, slug, machine, error_class=ValidationError):
    """
    Validations for a new slug of a version of the given project.

    This is in a separate function so we can use it in the clean method of the model
    (used in forms and the admin), and in the Django Rest Framework serializer (used in the API).
    Since DRF doesn't call the clean method of the model.

    Callers are expected to run it only when the slug is set or changed;
    slugs that are already in the database are never re-validated.
    """
    # We rely on the slug to identify versions managed by Read the Docs
    # (``latest`` and ``stable``), so it can't be changed.
    if machine:
        raise error_class(
            {"slug": _("The slug of versions managed by Read the Docs can't be changed.")}
        )

    normalized_slug = generate_version_slug(slug)
    if slug != normalized_slug:
        raise error_class(
            {
                "slug": _(
                    "The slug can contain lowercase letters, numbers, dots, dashes or underscores, "
                    "and it must start with a lowercase letter or a number. "
                    "Consider using '%(slug)s'."
                )
                % {"slug": normalized_slug}
            }
        )

    # NOTE: Django already checks the unique constraint,
    # but that message isn't attached to the slug field.
    # So we do the check here to provide a better error message.
    if project.versions.filter(slug=slug).exclude(pk=pk).exists():
        raise error_class({"slug": _("A version with that slug already exists.")})


def generate_unique_version_slug(source, version):
    slug = generate_version_slug(source) or "unknown"
    queryset = version.project.versions.all()
    if version.pk:
        queryset = queryset.exclude(pk=version.pk)
    base_slug = slug
    iteration = 0
    while queryset.filter(slug=slug).exists():
        suffix = _uniquifying_suffix(iteration)
        slug = f"{base_slug}_{suffix}"
        iteration += 1
    return slug


def generate_version_slug(source):
    normalized = _normalize(source)
    ok_chars = "-._"  # dash, dot, underscore
    slugified = unicode_slugify(
        normalized,
        only_ascii=True,
        spaces=False,
        lower=True,
        ok=ok_chars,
        space_replacement="-",
    )
    # Remove first character wile it's an invalid character for the beginning of the slug.
    slugified = slugified.lstrip(ok_chars)
    return slugified


def _normalize(value):
    """
    Normalize some invalid characters (/, %, !, ?) to become a dash (``-``).

    .. note::

        We replace these characters to a dash to keep compatibility with the
        old behavior and also because it makes this more readable.

    For example, ``release/1.0`` will become ``release-1.0``.
    """
    return re.sub("[/%!?]", "-", value)


def _uniquifying_suffix(iteration):
    """
    Create a unique suffix.

    This creates a suffix based on the number given as ``iteration``. It
    will return a value encoded as lowercase ascii letter. So we have an
    alphabet of 26 letters. The returned suffix will be for example ``yh``
    where ``yh`` is the encoding of ``iteration``. The length of it will be
    ``math.log(iteration, 26)``.

    Examples::

        uniquifying_suffix(0) == 'a'
        uniquifying_suffix(25) == 'z'
        uniquifying_suffix(26) == 'ba'
        uniquifying_suffix(52) == 'ca'
    """
    alphabet = string.ascii_lowercase
    length = len(alphabet)
    if iteration == 0:
        power = 0
    else:
        power = int(math.log(iteration, length))
    current = iteration
    suffix = ""
    for exp in reversed(list(range(0, power + 1))):
        digit = int(truediv(current, length**exp))
        suffix += alphabet[digit]
        current = current % length**exp
    return suffix
