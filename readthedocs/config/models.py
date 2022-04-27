"""Models for the response of the configuration object."""

from readthedocs.config.utils import to_dict


class Base:

    """
    Base class for every configuration.

    Each inherited class should define
    its attributes in the `__slots__` attribute.

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

    __slots__ = ('image', 'apt_packages')

    def __init__(self, **kwargs):
        kwargs.setdefault('apt_packages', [])
        super().__init__(**kwargs)


class BuildWithTools(Base):

    __slots__ = ("os", "tools", "jobs", "apt_packages", "commands")

    def __init__(self, **kwargs):
        kwargs.setdefault("apt_packages", [])
        kwargs.setdefault("commands", [])
        super().__init__(**kwargs)


class BuildTool(Base):

    __slots__ = ('version', 'full_version')


class BuildJobs(Base):

    """Object used for `build.jobs` key."""

    __slots__ = (
        "pre_checkout",
        "post_checkout",
        "pre_system_dependencies",
        "post_system_dependencies",
        "pre_create_environment",
        "post_create_environment",
        "pre_install",
        "post_install",
        "pre_build",
        "post_build",
    )

    def __init__(self, **kwargs):
        """
        Create an empty list as a default for all possible builds.jobs configs.

        This is necessary because it makes the code cleaner when we add items to these lists,
        without having to check for a dict to be created first.
        """
        for step in self.__slots__:
            kwargs.setdefault(step, [])
        super().__init__(**kwargs)


class Python(Base):

    __slots__ = ('version', 'install', 'use_system_site_packages')


class PythonInstallRequirements(Base):

    __slots__ = ('requirements',)


class PythonInstall(Base):

    __slots__ = (
        'path',
        'method',
        'extra_requirements',
    )


class Conda(Base):

    __slots__ = ('environment',)


class Sphinx(Base):

    __slots__ = ('builder', 'configuration', 'fail_on_warning')


class Mkdocs(Base):

    __slots__ = ('configuration', 'fail_on_warning')


class Submodules(Base):

    __slots__ = ('include', 'exclude', 'recursive')


class Search(Base):

    __slots__ = ('ranking', 'ignore')
