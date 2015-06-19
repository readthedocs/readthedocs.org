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

import re


# Regex breakdown:
#   \w -- start with alphanumeric value
#   [-._\w] -- allow dash, dot, underscore, digit, lowercase ascii
#   +? -- allow multiple of those, but be not greedy about the matching
#   (?: ... ) -- wrap everything so that the pattern cannot escape when used in
#                regexes.
VERSION_SLUG_REGEX = '(?:\w[-._\w]+?)'


version_slug_regex = re.compile(VERSION_SLUG_REGEX)
