"""
Models for the response of the configuration object.

We make use of pydantic to define the models/dataclasses for all the
options that the user can define in the configuration file.

Pydantic does runtime type checking and validation,
but we aren't using it yet, and instead we are doing the validation
in a separate step.
"""

from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


class ConfigBaseModel(BaseModel):
    """
    Base class for all the models used in the configuration object.

    Useful to define common configuration options for all the models.
    """

    model_config = ConfigDict(
        # Don't allow extra fields in the models.
        # It will raise an error if there are extra fields.
        extra="forbid",
    )


class BuildTool(ConfigBaseModel):
    version: str
    full_version: str


class BuildJobsBuildTypes(ConfigBaseModel):
    """Object used for `build.jobs.build` key."""

    html: list[str] | None = None
    pdf: list[str] | None = None
    epub: list[str] | None = None
    htmlzip: list[str] | None = None


class BuildJobs(ConfigBaseModel):
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


# TODO: rename this class to `Build`
class BuildWithOs(ConfigBaseModel):
    os: str
    tools: dict[str, BuildTool]
    jobs: BuildJobs = BuildJobs()
    apt_packages: list[str] = []
    commands: list[str] = []


class PythonInstallRequirements(ConfigBaseModel):
    requirements: str


class PythonInstall(ConfigBaseModel):
    path: str
    method: Literal["pip", "setuptools"] = "pip"
    extra_requirements: list[str] = []


class Python(ConfigBaseModel):
    install: list[PythonInstall | PythonInstallRequirements] = []


class Conda(ConfigBaseModel):
    environment: str


class Sphinx(ConfigBaseModel):
    configuration: str | None
    # NOTE: This is how we save the object in the DB,
    # the actual options for users are "html", "htmldir", "singlehtml".
    builder: Literal["sphinx", "sphinx_htmldir", "sphinx_singlehtml"] = "sphinx"
    fail_on_warning: bool = False


class Mkdocs(ConfigBaseModel):
    configuration: str | None
    fail_on_warning: bool = False


class Submodules(ConfigBaseModel):
    include: list[str] | Literal["all"] = []
    exclude: list[str] | Literal["all"] = []
    recursive: bool = False


class Search(ConfigBaseModel):
    ranking: dict[str, int] = {}
    ignore: list[str] = [
        "search.html",
        "search/index.html",
        "404.html",
        "404/index.html",
    ]
