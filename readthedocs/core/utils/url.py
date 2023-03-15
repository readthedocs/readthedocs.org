"""URL handling utilities."""

import re
from readthedocs.constants import pattern_opts


def unsafe_join_url_path(base, *args):
    """
    Joins a base URL path with one or more path components.

    This does a simple join of the base path with the path components,
    inserting a slash between each component.
    The resulting path will always start with a slash.

    .. warning::

       This does not offer protection against directory traversal attacks,
       it simply joins the path components together. This shouldn't be used
       to serve files, use ``readthedocs.storage.utils.safe_join`` for that.
    """
    base = "/" + base.lstrip("/")
    for path in args:
        base = base.rstrip("/") + "/" + path.lstrip("/")
    return base


def urlpattern_to_regex(urlpattern):
    """
    Transform a URL pattern to a regular expression.

    A URL pattern is a regular expression with replacement fields, like:
    language, version, filename, subproject.

    Before compiling the regular expression, the string is formatted with
    `str.format` to replace each field with a capture group:
    language, version, filename, project.

    This regex is mainly used by the unresolver.

    For example:

        ^/{language}/{version}$

    Would be transformed to:

        ^/(?P<language>en|es|br)/(?P<version>[a-zA-Z]+)$
    """
    return re.compile(urlpattern.format(
        language=f"(?P<language>{pattern_opts['lang_slug']})",
        version=f"(?P<version>{pattern_opts['version_slug']})",
        filename=f"(?P<filename>{pattern_opts['filename_slug']})",
        subproject=f"(?P<subproject>{pattern_opts['project_slug']})",
    ))


def urlpattern_to_plain_text(urlpattern):
    """
    Remove all regex special characters from a URL pattern.

    URL patterns are regular expressions with replacement fields,
    we remove all special regex characters to have a plain text
    representation of the URL. Replacement fields are left untouched.

    For example:

        ^/{language}/{version}$

    Would be transformed to:

        /{language}/{version}

    .. note::

       To escape a regex instead of removing its characters, use ``re.escape``.
    """
    remove = {"(", ")", "?", "$", "^"}
    plain_urlpattern = []
    is_escaped = False
    for c in urlpattern:
        # If the character is escaped, we don't
        # need to check if it's a special.
        if is_escaped:
            is_escaped = False
            plain_urlpattern.append(c)
            continue

        if c == "\\":
            is_escaped = True
            continue

        if c not in remove:
            plain_urlpattern.append(c)

    return "".join(plain_urlpattern)
