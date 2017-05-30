"""Class based settings for complex settings inheritance"""

from __future__ import absolute_import
from builtins import object
import inspect
import sys


class Settings(object):

    """Class-based settings wrapper"""

    @classmethod
    def load_settings(cls, module_name):
        """Export class variables and properties to module namespace

        This will export and class variable that is all upper case and doesn't
        begin with ``_``. These members will be set as attributes on the module
        ``module_name``.
        """
        self = cls()
        module = sys.modules[module_name]
        for (member, value) in inspect.getmembers(self):
            if member.isupper() and not member.startswith('_'):
                if isinstance(value, property):
                    value = value.fget(self)
                setattr(module, member, value)
