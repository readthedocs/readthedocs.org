"""Patterns for extending Read the Docs"""

import inspect

from django.conf import settings
from django.utils.module_loading import import_by_path


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

    _default_class = None
    _override_setting = None

    def __new__(cls, *args, **kwargs):
        """Set up wrapped object

        This is called when attributes are accessed on :py:class:`LazyObject`
        and the underlying wrapped object does not yet exist.
        """
        cls_new = cls._default_class
        cls_path = (getattr(settings, 'CLASS_OVERRIDES', {})
                    .get(cls._get_class_id()))
        if cls_path is None and cls._override_setting is not None:
            cls_path = getattr(settings, cls._override_setting, None)
        if cls_path is not None:
            cls_new = import_by_path(cls_path)
        return cls_new(*args, **kwargs)

    @classmethod
    def _get_class_id(cls):
        # type() here, because LazyObject overrides some attribute access
        return '.'.join([inspect.getmodule(cls).__name__, cls.__name__])
