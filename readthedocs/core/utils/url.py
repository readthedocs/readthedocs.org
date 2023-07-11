"""URL handling utilities."""


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
