"""Models for the response of the configuration object."""

from __future__ import division, print_function, unicode_literals


class Base(object):

    """
    Base class for every configuration.

    Each inherited class should define
    its attibutes in the `__slots__` attribute.
    """

    def __init__(self, **kwargs):
        for name in self.__slots__:
            setattr(self, name, kwargs[name])

    def as_dict(self):
        return {
            name: self.to_dict(getattr(self, name))
            for name in self.__slots__
        }

    def to_dict(self, value):
        """Recursively transform the class to a dict."""
        if hasattr(value, 'as_dict'):
            return value.as_dict()
        if isinstance(value, list):
            return [
                self.to_dict(e)
                for e in value
            ]
        if isinstance(value, dict):
            return {
                k: self.to_dict(v)
                for k, v in value.items()
            }
        return value


class Build(Base):

    __slots__ = ('image',)


class Python(Base):

    __slots__ = ('version', 'install', 'use_system_site_packages')


class PythonInstallRequirements(Base):

    __slots__ = ('requirements',)


class PythonInstall(Base):

    __slots__ = ('path', 'method', 'extra_requirements',)


class Conda(Base):

    __slots__ = ('environment',)


class Sphinx(Base):

    __slots__ = ('builder', 'configuration', 'fail_on_warning')


class Mkdocs(Base):

    __slots__ = ('configuration', 'fail_on_warning')


class Submodules(Base):

    __slots__ = ('include', 'exclude', 'recursive')
