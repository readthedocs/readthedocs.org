_DEFAULT = object()


def get_dotted_attribute(obj, attribute, default=_DEFAULT):
    """
    Allow to get nested attributes from an object using a dot notation.

    This behaves similar to getattr, but allows to get nested attributes.
    Similar, if a default value is provided, it will be returned if the
    attribute is not found, otherwise it will raise an AttributeError.
    """
    for attr in attribute.split("."):
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        elif default is not _DEFAULT:
            return default
        else:
            raise AttributeError(f"Object {obj} has no attribute {attr}")
    return obj


def has_dotted_attribute(obj, attribute):
    """Check if an object has a nested attribute using a dot notation."""
    try:
        get_dotted_attribute(obj, attribute)
        return True
    except AttributeError:
        return False
