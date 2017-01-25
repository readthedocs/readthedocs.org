"""Patterns for extending Read the Docs"""

import inspect

from django.conf import settings
from django.utils.module_loading import import_by_path


def get_override_class(proxy_class, default_class):
    class_id = '.'.join([
        inspect.getmodule(proxy_class).__name__,
        proxy_class.__name__
    ])
    class_path = getattr(settings, 'CLASS_OVERRIDES', {}).get(class_id)
    if class_path is None and proxy_class._override_setting is not None:
        class_path = getattr(settings, proxy_class._override_setting, None)
    if class_path is not None:
        default_class = import_by_path(class_path)
    return default_class


class SettingsOverrideMeta(type):

    """Meta class for passing along classmethod class to the underlying class"""

    def __getattr__(cls, attr):
        proxy_class = getattr(cls, '_default_class')
        return getattr(proxy_class, attr)


class SettingsOverrideObject(object):

    """Base class for creating class that can be overridden

    This is used for extension points in the code, where we want to extend a
    class without monkey patching it. This abstract class allows for lazy
    inheritance, creating a class from the specified class or from a setting,
    but only once the class is called.

    Default to an instance of the class defined by :py:cvar:`_default_class`.

    Next, look for an override setting class path in
    ``settings.CLASS_OVERRIDES``, which should be a dictionary of class paths.
    The setting should be a dictionary keyed by the object path name::

        CLASS_OVERRIDES = {
            'readthedocs.core.resolver.Resolver': 'something.resolver.Resolver',
        }

    Lastly, if ``settings.CLASS_OVERRIDES`` is missing, or the key is not found,
    attempt to pull the key :py:cvar:`_override_setting` from ``settings``.
    """

    __metaclass__ = SettingsOverrideMeta

    _default_class = None
    _override_setting = None

    def __new__(cls, *args, **kwargs):
        """Set up wrapped object

        Create an instance of the underlying proxy class and return instead of
        this class.
        """
        return get_override_class(cls, cls._default_class)(*args, **kwargs)
