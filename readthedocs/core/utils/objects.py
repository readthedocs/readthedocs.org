import functools


def cached_method(func):
    """
    Cache a method's return value on the instance it is called on.

    Use this instead of ``functools.lru_cache`` or ``functools.cache`` on
    methods. Those keep their entries on the class, keyed by the instance, so
    every instance the method was called on, and every argument passed to it,
    stays alive for the life of the process (and in views, the request and user
    with it). Entries here live in the instance ``__dict__`` and are released
    together with it.

    Arguments must be hashable, as with ``lru_cache``.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Per-instance dict, created on first use.
        cache = self.__dict__.setdefault("_cached_method_results", {})
        key = (func.__qualname__, args, frozenset(kwargs.items()))
        try:
            return cache[key]
        except KeyError:
            result = cache[key] = func(self, *args, **kwargs)
            return result

    return wrapper


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
