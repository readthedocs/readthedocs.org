"""
Models for the response of the configuration object.

We make use of pydantic to define the models/dataclasses for all the
options that the user can define in the configuration file.

Pydantic does runtime type checking and validation,
but we aren't using it yet, and instead we are doing the validation
in a separate step.
"""

import re
from enum import Enum
from typing import Literal

from django.conf import settings
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from readthedocs.config.exceptions import ConfigError
from readthedocs.config.validation import validate_choice, validate_path_pattern


class Parent(BaseModel):
    model_config = ConfigDict(extra="forbid")


# TODO: remove this
class BuildTool(Parent):
    version: str
    full_version: str


class BuildJobsBuildTypes(Parent):
    """Object used for `build.jobs.build` key."""

    html: list[str] | None = None
    pdf: list[str] | None = None
    epub: list[str] | None = None
    htmlzip: list[str] | None = None


class BuildJobs(Parent):
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
class BuildWithOs(Parent):
    os: str
    tools: dict[str, str]
    jobs: BuildJobs | None = None
    apt_packages: list[str] = []
    commands: list[str] | None = None

    @field_validator("os")
    @classmethod
    def validate_os(cls, value):
        validate_choice(value, settings.RTD_DOCKER_BUILD_SETTINGS["os"].keys())
        return value

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, value):
        tools = {}
        docker_settings = settings.RTD_DOCKER_BUILD_SETTINGS
        for tool, version in value.items():
            validate_choice(tool, docker_settings["tools"].keys())
            validate_choice(
                version, docker_settings["tools"][tool].keys()
            )
            tools[tool] = BuildTool(version=version, full_version=docker_settings["tools"][tool][version])
        return tools

    @field_validator("apt_packages")
    @classmethod
    def validate_apt_packages(cls, value):
        return [cls.validate_apt_package(package) for package in value]

    @classmethod
    def validate_apt_package(cls, package):
        """
        Validate the package name to avoid injections of extra options.

        We validate that they aren't interpreted as an option or file.
        See https://manpages.ubuntu.com/manpages/xenial/man8/apt-get.8.html
        and https://www.debian.org/doc/manuals/debian-reference/ch02.en.html#_debian_package_file_names  # noqa
        for allowed chars in packages names.
        """
        package = package.strip()
        invalid_starts = [
            # Don't allow extra options.
            "-",
            # Don't allow to install from a path.
            "/",
            ".",
        ]
        for start in invalid_starts:
            if package.startswith(start):
                raise ConfigError(
                    message_id=ConfigError.APT_INVALID_PACKAGE_NAME_PREFIX,
                    format_values={
                        "prefix": start,
                        "package": package,
                    },
                )

            # List of valid chars in packages names.
            pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.+-]*$")
            if not pattern.match(package):
                raise ConfigError(
                    message_id=ConfigError.APT_INVALID_PACKAGE_NAME,
                    format_values={
                        "package": package,
                    },
                )
        return package

    @model_validator(mode="after")
    def validate_jobs_and_commands_cant_be_used_together(self):
        if self.jobs and self.commands:
            raise ConfigError(
                message_id=ConfigError.BUILD_JOBS_AND_COMMANDS,
                format_values={
                    "key": "build",
                },
            )
        return self

    @model_validator(mode="after")
    def validate_tools_or_commands_are_used(self):
        if not self.tools and not self.commands:
            raise ConfigError(
                message_id=ConfigError.NOT_BUILD_TOOLS_OR_COMMANDS,
                format_values={
                    "key": "build",
                },
            )
        return self


class PythonInstallRequirements(Parent):
    requirements: str


class PythonInstall(Parent):
    path: str
    method: Literal["pip", "setuptools"] = "pip"
    extra_requirements: list[str] = []


class Python(Parent):
    install: list[PythonInstall | PythonInstallRequirements] = []


class Conda(Parent):
    environment: str



class Sphinx(Parent):
    configuration: str | None
    builder: Literal["html", "dirhtml", "singlehtml"] = "html"
    fail_on_warning: bool = False

    @field_validator("builder", mode="before")
    @classmethod
    def validate_builder(cls, value):
        # This is to keep compatibility with the old configuration.
        if value == "htmldir":
            return "dirhtml"
        return value


class Mkdocs(Parent):
    configuration: str | None
    fail_on_warning: bool = False


class Submodules(Parent):
    include: list[str] | Literal["all"] = []
    exclude: list[str] | Literal["all"] = []
    recursive: bool = False

    @model_validator(mode="after")
    def validate_include_exclude_together(self):
        if self.include and self.exclude:
            raise ConfigError(
                message_id=ConfigError.SUBMODULES_INCLUDE_EXCLUDE_TOGETHER,
            )
        return self


class Search(Parent):
    ranking: dict[str, int] = {}
    ignore: list[str] = [
        "search.html",
        "search/index.html",
        "404.html",
        "404/index.html",
    ]

    @field_validator("ranking")
    @classmethod
    def validate_ranking(cls, value):
        valid_rank_range = list(range(-10, 10 + 1))
        final_ranking = {}
        for pattern, rank in value.items():
            pattern = validate_path_pattern(pattern)
            validate_choice(rank, valid_rank_range)
            final_ranking[pattern] = rank
        return final_ranking

    @field_validator("ignore")
    @classmethod
    def validate_ignore(cls, value):
        return [validate_path_pattern(pattern) for pattern in value]


# TODO: replace with StrEnum when we upgrade to Python 3.11.
class Formats(str, Enum):
    pdf = "pdf"
    epub = "epub"
    htmlzip = "htmlzip"


class BuildConfig(Parent):

    version: Literal[2, "2"]
    formats: list[Formats] | Literal["all"] = []
    build: BuildWithOs

    conda: Conda | None = None
    python: Python | None = None

    sphinx: Sphinx | None = None
    mkdocs: Mkdocs | None = None
    submodules: Submodules = Submodules()
    search: Search = Search()

    @field_validator("formats", mode="before")
    @classmethod
    def validate_formats(cls, value):
        if value == "all":
            return [Formats.pdf, Formats.epub, Formats.htmlzip]
        return value

    @model_validator(mode="after")
    def validate_formats_matches_build_overrides(self):
        if not self.build.jobs:
            return self
        if self.build.jobs.build.pdf is not None and Formats.pdf not in self.formats:
            raise ConfigError(
                message_id=ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS,
                format_values={
                    "build_type": "pdf",
                },
            )
        if self.build.jobs.build.epub is not None and Formats.epub not in self.formats:
            raise ConfigError(
                message_id=ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS,
                format_values={
                    "build_type": "epub",
                },
            )
        if (
            self.build.jobs.build.htmlzip is not None
            and Formats.htmlzip not in self.formats
        ):
            raise ConfigError(
                message_id=ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS,
                format_values={
                    "build_type": "epub",
                },
            )
        return self

    @model_validator(mode="after")
    def validate_sphinx_and_mkdocs_cant_be_used_together(self):
        if self.sphinx and self.mkdocs:
            raise ConfigError(
                message_id=ConfigError.SPHINX_MKDOCS_CONFIG_TOGETHER,
            )
        return self

    @model_validator(mode="after")
    def validate_conda_if_using_conda_in_build_tools(self):
        if self.build.commands is not None and self.is_using_conda:
            raise ConfigError(
                message_id=ConfigError.CONDA_KEY_REQUIRED,
                format_values={"key": "conda"},
            )
        return self

    @property
    def is_using_conda(self):
        return self.python_interpreter in ["mamba", "conda"]

    @property
    def python_interpreter(self):
        tool = self.build.tools.get("python")
        if not tool:
            return None
        if tool.startswith("mamba"):
            return "mamba"
        if tool.startswith("miniconda"):
            return "conda"
        return "python"


def load(d):
    try:
        return BuildConfig(**d)
    except Exception as e:
        return e
