# Sentinel value to check if a default value was provided,
# so we can differentiate when None is provided as a default value
# and when it was not provided at all.
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
