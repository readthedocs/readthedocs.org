"""Class based settings for complex settings inheritance."""

import inspect
import sys
import os


class Settings:

    """Class-based settings wrapper."""

    read_only_settings = []

    @classmethod
    def load_settings(cls, module_name):
        """
        Export class variables and properties to module namespace.

        This will export any class variable that is all upper case and doesn't
        begin with ``_``. These members will be set as attributes on the module
        ``module_name``, which is the settings pattern that Django expects.

        Before exporting, ``local_settings`` is import and the module attributes
        are set on an instance of this class (or a subclass of this class). This
        is done to provide the settings and setting properties on this class to
        alter based on input from a ``local_settings`` file. Any setting in
        ``read_only_settings`` will be skipped, as we also need a method to
        ignore changes coming from ``local_settings`` -- for instance,
        your database is most likely defined in ``local_settings``, however we
        need to ensure this setting is always the default value in the settings
        for the build instance.
        """

        def copy_setting_attrs(source, target, skip=[]):
            for (member, value) in inspect.getmembers(source):
                if all([
                    member.isupper(),
                    not member.startswith('_'),
                    not member in skip,
                ]):
                    if isinstance(value, property):
                        value = value.fget(self)
                    setattr(target, member, value)

        if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
            try:
                from readthedocs.settings import local_settings
                copy_setting_attrs(
                    local_settings,
                    cls,
                    skip=cls.read_only_settings,
                )
            except ImportError:
                pass

        self = cls()
        module = sys.modules[module_name]
        copy_setting_attrs(self, module)
