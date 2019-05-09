# -*- coding: utf-8 -*-

"""Models for the response of the configuration object."""

from readthedocs.config.utils import to_dict


class Base:

    """
    Base class for every configuration.

    Each inherited class should define
    its attibutes in the `__slots__` attribute.

    We are using `__slots__` so we can't add more attributes by mistake,
    this is similar to a namedtuple.
    """

    def __init__(self, **kwargs):
        for name in self.__slots__:
            setattr(self, name, kwargs[name])

    def as_dict(self):
        return {
            name: to_dict(getattr(self, name))
            for name in self.__slots__
        }


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
