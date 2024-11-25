"""Models for the response of the configuration object."""
from pydantic import BaseModel

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
        return {name: to_dict(getattr(self, name)) for name in self.__slots__}


# TODO: rename this class to `Build`
class BuildWithOs(Base):
    __slots__ = ("os", "tools", "jobs", "apt_packages", "commands")

    def __init__(self, **kwargs):
        kwargs.setdefault("apt_packages", [])
        kwargs.setdefault("commands", [])
        super().__init__(**kwargs)


class BuildTool(Base):
    __slots__ = ("version", "full_version")


class BuildJobsBuildTypes(BaseModel):

    """Object used for `build.jobs.build` key."""

    html: list[str] | None = None
    pdf: list[str] | None = None
    epub: list[str] | None = None
    htmlzip: list[str] | None = None

    def as_dict(self):
        # Just to keep compatibility with the old implementation.
        return self.model_dump()


class BuildJobs(BaseModel):

    """Object used for `build.jobs` key."""

    pre_checkout: list[str] = []
    post_checkout: list[str] = []
    pre_system_dependencies: list[str] = []
    post_system_dependencies: list[str] = []
    pre_create_environment: list[str] = []
    create_environment: list[str] | None = None
    post_create_environment: list[str] = []
    pre_install: list[str] = []
    install: list[str] | None = None
    post_install: list[str] = []
    pre_build: list[str] = []
    build: BuildJobsBuildTypes = BuildJobsBuildTypes()
    post_build: list[str] = []

    def as_dict(self):
        # Just to keep compatibility with the old implementation.
        return self.model_dump()


class Python(Base):
    __slots__ = ("install",)


class PythonInstallRequirements(Base):
    __slots__ = ("requirements",)


class PythonInstall(Base):
    __slots__ = (
        "path",
        "method",
        "extra_requirements",
    )


class Conda(Base):
    __slots__ = ("environment",)


class Sphinx(Base):
    __slots__ = ("builder", "configuration", "fail_on_warning")


class Mkdocs(Base):
    __slots__ = ("configuration", "fail_on_warning")


class Submodules(Base):
    __slots__ = ("include", "exclude", "recursive")


class Search(Base):
    __slots__ = ("ranking", "ignore")
