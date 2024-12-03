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


class BuildTool(BaseModel):
    version: str
    full_version: str


class BuildJobsBuildTypes(BaseModel):
    """Object used for `build.jobs.build` key."""

    html: list[str] | None = None
    pdf: list[str] | None = None
    epub: list[str] | None = None
    htmlzip: list[str] | None = None


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


# TODO: rename this class to `Build`
class BuildWithOs(BaseModel):
    os: str
    tools: dict[str, BuildTool]
    jobs: BuildJobs = BuildJobs()
    apt_packages: list[str] = []
    commands: list[str] = []


class PythonInstallRequirements(BaseModel):
    requirements: str


class PythonInstall(BaseModel):
    path: str
    method: Literal["pip", "setuptools"] = "pip"
    extra_requirements: list[str] = []


class Python(BaseModel):
    install: list[PythonInstall | PythonInstallRequirements] = []


class Conda(BaseModel):
    environment: str


class Sphinx(BaseModel):
    configuration: str | None
    # NOTE: This is how we save the object in the DB,
    # the actual options for users are "html", "htmldir", "singlehtml".
    builder: Literal["sphinx", "sphinx_htmldir", "sphinx_singlehtml"] = "sphinx"
    fail_on_warning: bool = False


class Mkdocs(BaseModel):
    configuration: str | None
    fail_on_warning: bool = False


class Submodules(BaseModel):
    include: list[str] | Literal["all"] = []
    exclude: list[str] | Literal["all"] = []
    recursive: bool = False


class Search(BaseModel):
    ranking: dict[str, int] = {}
    ignore: list[str] = [
        "search.html",
        "search/index.html",
        "404.html",
        "404/index.html",
    ]
