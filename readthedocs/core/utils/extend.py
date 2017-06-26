"""Patterns for extending Read the Docs"""

from __future__ import absolute_import
import inspect

from django.conf import settings
from django.utils.module_loading import import_string
import six


def get_override_class(proxy_class, default_class=None):
    """Determine which class to use in an override class

    The `proxy_class` is the main class that is used, and `default_class` is the
    default class that this proxy class will instantiate.  If `default_class` is
    not defined, this will be inferred from the `proxy_class`, as is defined in
    :py:cls:`SettingsOverrideObject`.
    """
    if default_class is None:
        default_class = getattr(proxy_class, '_default_class')
    class_id = '.'.join([
        inspect.getmodule(proxy_class).__name__,
        proxy_class.__name__
    ])
    class_path = getattr(settings, 'CLASS_OVERRIDES', {}).get(class_id)
    # pylint: disable=protected-access
    if class_path is None and proxy_class._override_setting is not None:
        class_path = getattr(settings, proxy_class._override_setting, None)
    if class_path is not None:
        default_class = import_string(class_path)
    return default_class


class SettingsOverrideMeta(type):

    """Meta class for passing along classmethod class to the underlying class"""

    def __getattr__(cls, attr):  # noqa: pep8 false positive
        proxy_class = get_override_class(cls, getattr(cls, '_default_class'))
        return getattr(proxy_class, attr)


class SettingsOverrideObject(six.with_metaclass(SettingsOverrideMeta, object)):

    """Base class for creating class that can be overridden

    This is used for extension points in the code, where we want to extend a
    class without monkey patching it. This class will proxy classmethod calls
    and instantiation to an underlying class, determined by used of
    :py:cvar:`_default_class` or an override class from settings.

    The default target class is defined by :py:cvar:`_default_class`.

    To override this class, an override setting class path can be added to
    ``settings.CLASS_OVERRIDES``. This settings should be a dictionary keyed by
    source class paths, with values to the override classes::

        CLASS_OVERRIDES = {
            'readthedocs.core.resolver.Resolver': 'something.resolver.Resolver',
        }

    Lastly, if ``settings.CLASS_OVERRIDES`` is missing, or the key is not found,
    attempt to pull the key :py:cvar:`_override_setting` from ``settings``. This
    matches the pattern we've been using previously.
    """

    _default_class = None
    _override_setting = None

    def __new__(cls, *args, **kwargs):
        """Set up wrapped object

        Create an instance of the underlying target class and return instead of
        this class.
        """
        return get_override_class(cls, cls._default_class)(*args, **kwargs)
