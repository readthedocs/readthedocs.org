"""URL hadling utilities."""


def join_url_path(base, *args):
    """
    Joins a base URL path with one or more path components.

    This does a simple join of the base path with the path components,
    inserting a slash between each component.
    It does not offer protection against directory traversal attacks.
    """
    base = "/" + base.lstrip("/")
    for path in args:
        base = base.rstrip("/") + "/" + path.lstrip("/")
    return base
