"""Build configuration for rtd."""

import copy
import datetime
import os
import re
from contextlib import contextmanager
from functools import lru_cache

import pytz
from django.conf import settings
from pydantic import BaseModel

from readthedocs.config.utils import list_to_dict
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.projects.constants import GENERIC

from .exceptions import ConfigError
from .exceptions import ConfigValidationError
from .find import find_one
from .models import BuildJobs
from .models import BuildJobsBuildTypes
from .models import BuildTool
from .models import BuildWithOs
from .models import Conda
from .models import Mkdocs
from .models import Python
from .models import PythonInstall
from .models import Search
from .models import Sphinx
from .models import Submodules
from .parser import ParseError
from .parser import parse
from .validation import validate_bool
from .validation import validate_choice
from .validation import validate_dict
from .validation import validate_list
from .validation import validate_path
from .validation import validate_path_pattern
from .validation import validate_string


__all__ = (
    "ALL",
    "load",
    "BuildConfigV2",
    "PIP",
    "SETUPTOOLS",
    "LATEST_CONFIGURATION_VERSION",
)

ALL = "all"
PIP = "pip"
SETUPTOOLS = "setuptools"
CONFIG_FILENAME_REGEX = r"^\.?readthedocs.ya?ml$"

LATEST_CONFIGURATION_VERSION = 2


class BuildConfigBase:
    """
    Config that handles the build of one particular documentation.

    .. note::

       You need to call ``validate`` before the config is ready to use.

    :param raw_config: A dict with all configuration without validation.
    :param source_file: The file that contains the configuration.
                        All paths are relative to this file.
                        If a dir is given, the configuration was loaded
                        from another source (like the web admin).
    """

    PUBLIC_ATTRIBUTES = [
        "version",
        "formats",
        "python",
        "conda",
        "build",
        "doctype",
        "sphinx",
        "mkdocs",
        "submodules",
        "search",
    ]

    version = None

    def __init__(
        self,
        raw_config,
        source_file,
        base_path=None,
        deprecate_implicit_keys=None,
    ):
        self._raw_config = copy.deepcopy(raw_config)
        self.source_config = copy.deepcopy(raw_config)
        self.source_file = source_file
        # Support explicit base_path as well as implicit base_path from config_file.
        if base_path:
            self.base_path = base_path
        else:
            if os.path.isdir(self.source_file):
                self.base_path = self.source_file
            else:
                self.base_path = os.path.dirname(self.source_file)

        self._config = {}

        if deprecate_implicit_keys is not None:
            self.deprecate_implicit_keys = deprecate_implicit_keys
        elif settings.RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS:
            tzinfo = pytz.timezone("America/Los_Angeles")
            now = datetime.datetime.now(tz=tzinfo)
            # Dates as per https://about.readthedocs.com/blog/2024/12/deprecate-config-files-without-sphinx-or-mkdocs-config/
            # fmt: off
            self.deprecate_implicit_keys = (
                # 12 hours brownout.
                datetime.datetime(2025, 1, 6, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2025, 1, 6, 12, 0, 0, tzinfo=tzinfo)
                # 24 hours brownout.
                or datetime.datetime(2025, 1, 13, 0, 0, 0, tzinfo=tzinfo) < now < datetime.datetime(2025, 1, 14, 0, 0, 0, tzinfo=tzinfo)
                # Permanent removal.
                or datetime.datetime(2025, 1, 20, 0, 0, 0, tzinfo=tzinfo) < now
            )
            # fmt: on
        else:
            self.deprecate_implicit_keys = False

    @contextmanager
    def catch_validation_error(self, key):
        """Catch a ``ConfigValidationError`` and raises a ``ConfigError`` error."""
        # NOTE: I don't like too much this pattern of re-raising an exception via a context manager.
        # I think we should raise the exception where it happens, instead of encapsulating all of them.
        # The only small limitation that I found is the requirement of passing ``key`` down to where
        # the exception happens.
        # I'm keeping this pattern for now until we decide to refactor it.
        try:
            yield
        except ConfigValidationError as error:
            # Expand the format values defined when the exception is risen
            # with extra ones we have here
            format_values = getattr(error, "format_values", {})
            format_values.update(
                {
                    "key": key,
                    "value": error.format_values.get("value"),
                    "source_file": os.path.relpath(self.source_file, self.base_path),
                }
            )

            raise ConfigError(
                message_id=error.message_id,
                format_values=format_values,
            ) from error

    def pop(self, name, container, default, raise_ex):
        """
        Search and pop a key inside a dict.

        This will pop the keys recursively if the container is empty.

        :param name: the key name in a list form (``['key', 'inner']``)
        :param container: a dictionary that contains the key
        :param default: default value to return if the key doesn't exists
        :param raise_ex: if True, raises an exception when a key is not found
        """
        key = name[0]
        validate_dict(container)
        if key in container:
            if len(name) > 1:
                value = self.pop(name[1:], container[key], default, raise_ex)
                if not container[key]:
                    container.pop(key)
            else:
                value = container.pop(key)
            return value
        if raise_ex:
            raise ConfigValidationError(
                message_id=ConfigValidationError.VALUE_NOT_FOUND,
                format_values={
                    "value": key,
                },
            )
        return default

    def pop_config(self, key, default=None, raise_ex=False):
        """
        Search and pop a key (recursively) from `self._raw_config`.

        :param key: the key name in a dotted form (``key.innerkey``)
        :param default: Optionally, it can receive a default value
        :param raise_ex: If True, raises an exception when the key is not found
        """
        return self.pop(key.split("."), self._raw_config, default, raise_ex)

    def validate(self):
        raise NotImplementedError()

    @property
    def is_using_conda(self):
        return self.python_interpreter in ("conda", "mamba")

    @property
    def is_using_build_commands(self):
        return self.build.commands != []

    @property
    def is_using_setup_py_install(self):
        """Check if this project is using `setup.py install` as installation method."""
        for install in self.python.install:
            if isinstance(install, PythonInstall) and install.method == SETUPTOOLS:
                return True
        return False

    @property
    def python_interpreter(self):
        tool = self.build.tools.get("python")
        if tool and tool.version.startswith("mamba"):
            return "mamba"
        if tool and tool.version.startswith("miniconda"):
            return "conda"
        if tool:
            return "python"
        return None

    @property
    def docker_image(self):
        return self.settings["os"][self.build.os]

    def as_dict(self):
        config = {}
        for name in self.PUBLIC_ATTRIBUTES:
            attr = getattr(self, name)
            config[name] = attr.model_dump() if isinstance(attr, BaseModel) else attr
        return config

    def __getattr__(self, name):
        """Raise an error for unknown attributes."""
        raise ConfigError(
            message_id=ConfigError.KEY_NOT_SUPPORTED_IN_VERSION,
            format_values={"key": name},
        )


class BuildConfigV2(BuildConfigBase):
    """Version 2 of the configuration file."""

    version = "2"
    valid_formats = ["htmlzip", "pdf", "epub"]
    valid_install_method = [PIP, SETUPTOOLS]
    valid_sphinx_builders = {
        "html": "sphinx",
        "htmldir": "sphinx_htmldir",
        "dirhtml": "sphinx_htmldir",
        "singlehtml": "sphinx_singlehtml",
    }

    @property
    def settings(self):
        return settings.RTD_DOCKER_BUILD_SETTINGS

    def validate(self):
        """Validates and process ``raw_config``."""
        self._config["formats"] = self.validate_formats()

        # This should be called before ``validate_python`` and ``validate_conda``
        self._config["build"] = self.validate_build()

        self._config["conda"] = self.validate_conda()
        self._config["python"] = self.validate_python()
        # Call this before validate sphinx and mkdocs
        self.validate_doc_types()
        self._config["mkdocs"] = self.validate_mkdocs()
        self._config["sphinx"] = self.validate_sphinx()
        self._config["submodules"] = self.validate_submodules()
        self._config["search"] = self.validate_search()
        if self.deprecate_implicit_keys:
            self.validate_deprecated_implicit_keys()
        self.validate_keys()

    def validate_formats(self):
        """
        Validates that formats contains only valid formats.

        The ``ALL`` keyword can be used to indicate that all formats are used.
        We ignore the default values here.
        """
        formats = self.pop_config("formats", [])
        if formats == ALL:
            return self.valid_formats
        with self.catch_validation_error("formats"):
            validate_list(formats)
            for format_ in formats:
                validate_choice(format_, self.valid_formats)
        return formats

    def validate_conda(self):
        """Validates the conda key."""
        raw_conda = self._raw_config.get("conda")
        if raw_conda is None:
            if self.is_using_conda and not self.is_using_build_commands:
                raise ConfigError(
                    message_id=ConfigError.CONDA_KEY_REQUIRED,
                    format_values={"key": "conda"},
                )
            return None

        with self.catch_validation_error("conda"):
            validate_dict(raw_conda)

        conda = {}
        with self.catch_validation_error("conda.environment"):
            environment = self.pop_config("conda.environment", raise_ex=True)
            conda["environment"] = validate_path(environment, self.base_path)
        return conda

    # TODO: rename these methods to call them just `validate_build_config`
    def validate_build_config_with_os(self):
        """
        Validates the build object (new format).

        At least one element must be provided in ``build.tools``.
        """
        build = {}
        with self.catch_validation_error("build.os"):
            build_os = self.pop_config("build.os", raise_ex=True)
            build["os"] = validate_choice(build_os, self.settings["os"].keys())

        tools = {}
        with self.catch_validation_error("build.tools"):
            tools = self.pop_config("build.tools")
            if tools:
                validate_dict(tools)
                for tool in tools.keys():
                    validate_choice(tool, self.settings["tools"].keys())

        jobs = {}
        with self.catch_validation_error("build.jobs"):
            # FIXME: should we use `default={}` or kept the `None` here and
            # shortcircuit the rest of the logic?
            jobs = self.pop_config("build.jobs", default={})
            validate_dict(jobs)
            # NOTE: besides validating that each key is one of the expected
            # ones, we could validate the value of each of them is a list of
            # commands. However, I don't think we should validate the "command"
            # looks like a real command.
            valid_jobs = list(BuildJobs.model_fields.keys())
            for job in jobs.keys():
                validate_choice(job, valid_jobs)

        commands = []
        with self.catch_validation_error("build.commands"):
            commands = self.pop_config("build.commands", default=[])
            validate_list(commands)

        if not (tools or commands):
            raise ConfigError(
                message_id=ConfigError.NOT_BUILD_TOOLS_OR_COMMANDS,
                format_values={
                    "key": "build",
                },
            )

        if commands and jobs:
            raise ConfigError(
                message_id=ConfigError.BUILD_JOBS_AND_COMMANDS,
                format_values={
                    "key": "build",
                },
            )

        build["jobs"] = {}

        with self.catch_validation_error("build.jobs.build"):
            build["jobs"]["build"] = self.validate_build_jobs_build(jobs)
        # Remove the build.jobs.build key from the build.jobs dict,
        # since it's the only key that should be a dictionary,
        # it was already validated above.
        jobs.pop("build", None)

        for job, job_commands in jobs.items():
            with self.catch_validation_error(f"build.jobs.{job}"):
                build["jobs"][job] = [
                    validate_string(job_command) for job_command in validate_list(job_commands)
                ]

        build["commands"] = []
        for command in commands:
            with self.catch_validation_error("build.commands"):
                build["commands"].append(validate_string(command))

        build["tools"] = {}
        if tools:
            for tool, version in tools.items():
                with self.catch_validation_error(f"build.tools.{tool}"):
                    build["tools"][tool] = validate_choice(
                        version,
                        self.settings["tools"][tool].keys(),
                    )

        build["apt_packages"] = self.validate_apt_packages()
        return build

    def validate_build_jobs_build(self, build_jobs):
        result = {}
        build_jobs_build = build_jobs.get("build", {})
        validate_dict(build_jobs_build)

        allowed_build_types = list(BuildJobsBuildTypes.model_fields.keys())
        for build_type, build_commands in build_jobs_build.items():
            validate_choice(build_type, allowed_build_types)
            if build_type != "html" and build_type not in self.formats:
                raise ConfigError(
                    message_id=ConfigError.BUILD_JOBS_BUILD_TYPE_MISSING_IN_FORMATS,
                    format_values={
                        "build_type": build_type,
                    },
                )
            with self.catch_validation_error(f"build.jobs.build.{build_type}"):
                result[build_type] = [
                    validate_string(build_command)
                    for build_command in validate_list(build_commands)
                ]

        return result

    def validate_apt_packages(self):
        apt_packages = []
        with self.catch_validation_error("build.apt_packages"):
            raw_packages = self._raw_config.get("build", {}).get("apt_packages", [])
            validate_list(raw_packages)
            # Transform to a dict, so is easy to validate individual entries.
            self._raw_config.setdefault("build", {})["apt_packages"] = list_to_dict(raw_packages)

            apt_packages = [self.validate_apt_package(index) for index in range(len(raw_packages))]
            if not raw_packages:
                self.pop_config("build.apt_packages")

        return apt_packages

    def validate_build(self):
        raw_build = self._raw_config.get("build", {})
        with self.catch_validation_error("build"):
            validate_dict(raw_build)
        return self.validate_build_config_with_os()

    def validate_apt_package(self, index):
        """
        Validate the package name to avoid injections of extra options.

        We validate that they aren't interpreted as an option or file.
        See https://manpages.ubuntu.com/manpages/xenial/man8/apt-get.8.html
        and https://www.debian.org/doc/manuals/debian-reference/ch02.en.html#_debian_package_file_names  # noqa
        for allowed chars in packages names.
        """
        key = f"build.apt_packages.{index}"
        package = self.pop_config(key)
        with self.catch_validation_error(key):
            validate_string(package)
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
                            "key": key,
                        },
                    )

            # List of valid chars in packages names.
            pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.+-]*$")
            if not pattern.match(package):
                raise ConfigError(
                    message_id=ConfigError.APT_INVALID_PACKAGE_NAME,
                    format_values={
                        "package": package,
                        "key": key,
                    },
                )
        return package

    def validate_python(self):
        """
        Validates the python key.

        validate_build should be called before this, since it initialize the
        build.image attribute.

        .. note::
           - ``version`` can be a string or number type.
           - ``extra_requirements`` needs to be used with ``install: 'pip'``.
        """
        raw_python = self._raw_config.get("python", {})
        with self.catch_validation_error("python"):
            validate_dict(raw_python)

        python = {}
        with self.catch_validation_error("python.install"):
            raw_install = self._raw_config.get("python", {}).get("install", [])
            validate_list(raw_install)
            if raw_install:
                # Transform to a dict, so it's easy to validate extra keys.
                self._raw_config.setdefault("python", {})["install"] = list_to_dict(raw_install)
            else:
                self.pop_config("python.install")

        raw_install = self._raw_config.get("python", {}).get("install", [])
        python["install"] = [
            self.validate_python_install(index) for index in range(len(raw_install))
        ]

        return python

    def validate_python_install(self, index):
        """Validates the python.install.{index} key."""
        python_install = {}
        key = "python.install.{}".format(index)
        raw_install = self._raw_config["python"]["install"][str(index)]
        with self.catch_validation_error(key):
            validate_dict(raw_install)

        if "requirements" in raw_install:
            requirements_key = key + ".requirements"
            with self.catch_validation_error(requirements_key):
                requirements = validate_path(
                    self.pop_config(requirements_key),
                    self.base_path,
                )
                python_install["requirements"] = requirements
        elif "path" in raw_install:
            path_key = key + ".path"
            with self.catch_validation_error(path_key):
                path = validate_path(
                    self.pop_config(path_key),
                    self.base_path,
                )
                python_install["path"] = path

            method_key = key + ".method"
            with self.catch_validation_error(method_key):
                method = validate_choice(
                    self.pop_config(method_key, PIP),
                    self.valid_install_method,
                )
                python_install["method"] = method

            extra_req_key = key + ".extra_requirements"
            with self.catch_validation_error(extra_req_key):
                extra_requirements = validate_list(
                    self.pop_config(extra_req_key, []),
                )
                if extra_requirements and python_install["method"] != PIP:
                    raise ConfigError(
                        message_id=ConfigError.USE_PIP_FOR_EXTRA_REQUIREMENTS,
                    )
                python_install["extra_requirements"] = extra_requirements
        else:
            raise ConfigError(
                message_id=ConfigError.PIP_PATH_OR_REQUIREMENT_REQUIRED,
                format_values={
                    "key": key,
                },
            )

        return python_install

    def validate_doc_types(self):
        """
        Validates that the user only have one type of documentation.

        This should be called before validating ``sphinx`` or ``mkdocs`` to
        avoid innecessary validations.
        """
        with self.catch_validation_error("."):
            if "sphinx" in self._raw_config and "mkdocs" in self._raw_config:
                raise ConfigError(
                    message_id=ConfigError.SPHINX_MKDOCS_CONFIG_TOGETHER,
                )

    def validate_mkdocs(self):
        """
        Validates the mkdocs key.

        It makes sure we are using an existing configuration file.
        """
        raw_mkdocs = self._raw_config.get("mkdocs")
        if raw_mkdocs is None:
            return None

        with self.catch_validation_error("mkdocs"):
            validate_dict(raw_mkdocs)

        mkdocs = {}
        with self.catch_validation_error("mkdocs.configuration"):
            configuration = self.pop_config("mkdocs.configuration", None)
            if configuration is not None:
                configuration = validate_path(configuration, self.base_path)
            mkdocs["configuration"] = configuration

        with self.catch_validation_error("mkdocs.fail_on_warning"):
            fail_on_warning = self.pop_config("mkdocs.fail_on_warning", False)
            mkdocs["fail_on_warning"] = validate_bool(fail_on_warning)

        return mkdocs

    def validate_sphinx(self):
        """
        Validates the sphinx key.

        It makes sure we are using an existing configuration file.

        .. note::
           It should be called after ``validate_mkdocs``. That way
           we can default to sphinx if ``mkdocs`` is not given.
        """
        raw_sphinx = self._raw_config.get("sphinx")
        if raw_sphinx is None:
            if self.mkdocs is None:
                raw_sphinx = {}
            else:
                return None

        with self.catch_validation_error("sphinx"):
            validate_dict(raw_sphinx)

        sphinx = {}
        with self.catch_validation_error("sphinx.builder"):
            builder = validate_choice(
                self.pop_config("sphinx.builder", "html"),
                self.valid_sphinx_builders.keys(),
            )
            sphinx["builder"] = self.valid_sphinx_builders[builder]

        with self.catch_validation_error("sphinx.configuration"):
            configuration = self.pop_config(
                "sphinx.configuration",
            )
            if configuration is not None:
                configuration = validate_path(configuration, self.base_path)
            sphinx["configuration"] = configuration

        with self.catch_validation_error("sphinx.fail_on_warning"):
            fail_on_warning = self.pop_config("sphinx.fail_on_warning", False)
            sphinx["fail_on_warning"] = validate_bool(fail_on_warning)

        return sphinx

    def validate_submodules(self):
        """
        Validates the submodules key.

        - We can use the ``ALL`` keyword in include or exclude.
        - We can't exclude and include submodules at the same time.
        """
        raw_submodules = self._raw_config.get("submodules", {})
        with self.catch_validation_error("submodules"):
            validate_dict(raw_submodules)

        submodules = {}
        with self.catch_validation_error("submodules.include"):
            include = self.pop_config("submodules.include", [])
            if include != ALL:
                include = [validate_string(submodule) for submodule in validate_list(include)]
            submodules["include"] = include

        with self.catch_validation_error("submodules.exclude"):
            default = [] if submodules["include"] else ALL
            exclude = self.pop_config("submodules.exclude", default)
            if exclude != ALL:
                exclude = [validate_string(submodule) for submodule in validate_list(exclude)]
            submodules["exclude"] = exclude

        with self.catch_validation_error("submodules"):
            is_including = bool(submodules["include"])
            is_excluding = submodules["exclude"] == ALL or bool(submodules["exclude"])
            if is_including and is_excluding:
                raise ConfigError(
                    message_id=ConfigError.SUBMODULES_INCLUDE_EXCLUDE_TOGETHER,
                )

        with self.catch_validation_error("submodules.recursive"):
            recursive = self.pop_config("submodules.recursive", False)
            submodules["recursive"] = validate_bool(recursive)

        return submodules

    def validate_search(self):
        """
        Validates the search key.

        - ``ranking`` is a map of path patterns to a rank.
        - ``ignore`` is a list of patterns.
        - The path pattern supports basic globs (*, ?, [seq]).
        - The rank can be a integer number between -10 and 10.
        """
        raw_search = self._raw_config.get("search", {})
        with self.catch_validation_error("search"):
            validate_dict(raw_search)

        search = {}
        with self.catch_validation_error("search.ranking"):
            ranking = self.pop_config("search.ranking", {})
            validate_dict(ranking)

            valid_rank_range = list(range(-10, 10 + 1))

            final_ranking = {}
            for pattern, rank in ranking.items():
                pattern = validate_path_pattern(pattern)
                validate_choice(rank, valid_rank_range)
                final_ranking[pattern] = rank

            search["ranking"] = final_ranking

        with self.catch_validation_error("search.ignore"):
            ignore_default = [
                "search.html",
                "search/index.html",
                "404.html",
                "404/index.html",
            ]
            search_ignore = self.pop_config("search.ignore", ignore_default)
            validate_list(search_ignore)

            final_ignore = [validate_path_pattern(pattern) for pattern in search_ignore]
            search["ignore"] = final_ignore

        return search

    def validate_deprecated_implicit_keys(self):
        """
        Check for deprecated usages and raise an exception if found.

        - If the user is using build.commands, we don't need the sphinx or mkdocs keys.
        - If the sphinx key is used, a path to the configuration file is required.
        - If the mkdocs key is used, a path to the configuration file is required.
        - If none of the sphinx or mkdocs keys are used,
          and the user isn't overriding the new build jobs,
          the sphinx key is explicitly required.
        """
        if self.is_using_build_commands:
            return

        has_sphinx_key = "sphinx" in self.source_config
        has_mkdocs_key = "mkdocs" in self.source_config
        if has_sphinx_key and not self.sphinx.configuration:
            raise ConfigError(
                message_id=ConfigError.SPHINX_CONFIG_MISSING,
            )

        if has_mkdocs_key and not self.mkdocs.configuration:
            raise ConfigError(
                message_id=ConfigError.MKDOCS_CONFIG_MISSING,
            )

        if not self.new_jobs_overriden and not has_sphinx_key and not has_mkdocs_key:
            raise ConfigError(
                message_id=ConfigError.SPHINX_CONFIG_MISSING,
            )

    @property
    def new_jobs_overriden(self):
        """Check if any of the new (undocumented) build jobs are overridden."""
        build_jobs = self.build.jobs
        new_jobs = (
            build_jobs.create_environment,
            build_jobs.install,
            build_jobs.build.html,
            build_jobs.build.pdf,
            build_jobs.build.epub,
            build_jobs.build.htmlzip,
        )
        for job in new_jobs:
            if job is not None:
                return True
        return False

    def validate_keys(self):
        """
        Checks that we don't have extra keys (invalid ones).

        This should be called after all the validations are done and all keys
        are popped from `self._raw_config`.
        """
        # The version key isn't popped, but it's
        # validated in `load`.
        self.pop_config("version", None)
        wrong_key = ".".join(self._get_extra_key(self._raw_config))
        if wrong_key:
            raise ConfigError(
                message_id=ConfigError.INVALID_KEY_NAME,
                format_values={
                    "key": wrong_key,
                },
            )

    def _get_extra_key(self, value):
        """
        Get the extra keyname (list form) of a dict object.

        If there is more than one extra key, the first one is returned.

        Example::

        {
            'key': {
                'name':  'inner',
            }
        }

        Will return `['key', 'name']`.
        """
        if isinstance(value, dict) and value:
            key_name = next(iter(value))
            return [key_name] + self._get_extra_key(value[key_name])
        return []

    @property
    def formats(self):
        return self._config["formats"]

    @property
    def conda(self):
        if self._config["conda"]:
            return Conda(**self._config["conda"])
        return None

    @property
    @lru_cache(maxsize=1)
    def build(self):
        build = self._config["build"]
        tools = {
            tool: BuildTool(
                version=version,
                full_version=self.settings["tools"][tool][version],
            )
            for tool, version in build["tools"].items()
        }
        return BuildWithOs(
            os=build["os"],
            tools=tools,
            jobs=BuildJobs(**build["jobs"]),
            commands=build["commands"],
            apt_packages=build["apt_packages"],
        )

    @property
    def python(self):
        return Python(**self._config["python"])

    @property
    def sphinx(self):
        if self._config["sphinx"]:
            return Sphinx(**self._config["sphinx"])
        return None

    @property
    def mkdocs(self):
        if self._config["mkdocs"]:
            return Mkdocs(**self._config["mkdocs"])
        return None

    @property
    def doctype(self):
        if "commands" in self._config["build"] and self._config["build"]["commands"]:
            return GENERIC

        has_sphinx_key = "sphinx" in self.source_config
        has_mkdocs_key = "mkdocs" in self.source_config
        if self.new_jobs_overriden and not has_sphinx_key and not has_mkdocs_key:
            return GENERIC

        if self.mkdocs:
            return "mkdocs"
        return self.sphinx.builder

    @property
    def submodules(self):
        return Submodules(**self._config["submodules"])

    @property
    def search(self):
        return Search(**self._config["search"])


def load(path, readthedocs_yaml_path=None):
    """
    Load a project configuration and the top-most build config for a given path.

    That is usually the root of the project, but will look deeper.
    """
    # Custom non-default config file location
    if readthedocs_yaml_path:
        filename = os.path.join(path, readthedocs_yaml_path)
        if not os.path.exists(filename):
            raise ConfigError(
                message_id=ConfigError.CONFIG_PATH_NOT_FOUND,
                format_values={"directory": os.path.relpath(filename, path)},
            )
    # Default behavior
    else:
        filename = find_one(path, CONFIG_FILENAME_REGEX)
        if not filename:
            raise ConfigError(ConfigError.DEFAULT_PATH_NOT_FOUND)

    # Allow symlinks, but only the ones that resolve inside the base directory.
    with safe_open(filename, "r", allow_symlinks=True, base_path=path) as configuration_file:
        try:
            config = parse(configuration_file.read())
        except ParseError as error:
            raise ConfigError(
                message_id=ConfigError.SYNTAX_INVALID,
                format_values={
                    "filename": os.path.relpath(filename, path),
                    "error_message": str(error),
                },
            ) from error

        version = config.get("version", 2)
        if version not in (2, "2"):
            raise ConfigError(message_id=ConfigError.INVALID_VERSION)

        build_config = BuildConfigV2(
            config,
            source_file=filename,
        )

    build_config.validate()
    return build_config
