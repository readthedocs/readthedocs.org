"""An abstraction over virtualenv and Conda environments."""

import copy
import os

import structlog
import yaml

from readthedocs.config import PIP
from readthedocs.config import SETUPTOOLS
from readthedocs.config import ParseError
from readthedocs.config import parse as parse_yaml
from readthedocs.config.models import PythonInstall
from readthedocs.config.models import PythonInstallRequirements
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.projects.constants import GENERIC
from readthedocs.projects.exceptions import UserFileNotFound
from readthedocs.projects.models import Feature


log = structlog.get_logger(__name__)


class PythonEnvironment:
    """An isolated environment into which Python packages can be installed."""

    def __init__(self, version, build_env, config=None):
        self.version = version
        self.project = version.project
        self.build_env = build_env
        if config:
            self.config = config
        else:
            self.config = load_yaml_config(version)
        # Compute here, since it's used a lot
        self.checkout_path = self.project.checkout_path(self.version.slug)
        structlog.contextvars.bind_contextvars(
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )

    def install_requirements(self):
        """Install all requirements from the config object."""
        for install in self.config.python.install:
            if isinstance(install, PythonInstallRequirements):
                self.install_requirements_file(install)
            if isinstance(install, PythonInstall):
                self.install_package(install)

    def install_package(self, install):
        """
        Install the package using pip or setuptools.

        :param install: A install object from the config module.
        :type install: readthedocs.config.models.PythonInstall
        """
        # NOTE: `venv_bin` requires `prefixes`.
        # However, it's overwritten in the subclasses and
        # it forces passing the `prefixes=` attribute.
        # I'm not sure how to solve this, so I'm skipping this check for now.
        # pylint: disable=no-value-for-parameter

        if install.method == PIP:
            # Prefix ./ so pip installs from a local path rather than pypi
            local_path = os.path.join(".", install.path) if install.path != "." else install.path
            extra_req_param = ""
            if install.extra_requirements:
                extra_req_param = "[{}]".format(",".join(install.extra_requirements))
            self.build_env.run(
                self.venv_bin(filename="python"),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--upgrade-strategy",
                "only-if-needed",
                "--no-cache-dir",
                "{path}{extra_requirements}".format(
                    path=local_path,
                    extra_requirements=extra_req_param,
                ),
                cwd=self.checkout_path,
                bin_path=self.venv_bin(),
            )
        elif install.method == SETUPTOOLS:
            self.build_env.run(
                self.venv_bin(filename="python"),
                os.path.join(install.path, "setup.py"),
                "install",
                "--force",
                cwd=self.checkout_path,
                bin_path=self.venv_bin(),
            )

    def venv_bin(self, prefixes, filename=None):
        """
        Return path to the virtualenv bin path, or a specific binary.

        :param filename: If specified, add this filename to the path return
        :param prefixes: List of path prefixes to include in the resulting path
        :returns: Path to virtualenv bin or filename in virtualenv bin
        """
        if filename is not None:
            prefixes.append(filename)
        return os.path.join(*prefixes)


class Virtualenv(PythonEnvironment):
    """
    A virtualenv_ environment.

    .. _virtualenv: https://virtualenv.pypa.io/
    """

    # pylint: disable=arguments-differ
    def venv_bin(self, filename=None):
        prefixes = ["$READTHEDOCS_VIRTUALENV_PATH", "bin"]
        return super().venv_bin(prefixes, filename=filename)

    def setup_base(self):
        """
        Create a virtualenv, invoking ``python -mvirtualenv``.

        .. note::

            ``--no-download`` was removed because of the pip breakage,
            it was sometimes installing pip 20.0 which broke everything
            https://github.com/readthedocs/readthedocs.org/issues/6585

            Important not to add empty string arguments, see:
            https://github.com/readthedocs/readthedocs.org/issues/7322
        """
        cli_args = [
            "-mvirtualenv",
            # Append the positional destination argument
            "$READTHEDOCS_VIRTUALENV_PATH",
        ]

        self.build_env.run(
            self.config.python_interpreter,
            *cli_args,
            # Don't use virtualenv bin that doesn't exist yet
            bin_path=None,
            # Don't use the project's root, some config files can interfere
            cwd=None,
        )

    def install_core_requirements(self):
        """Install basic Read the Docs requirements into the virtualenv."""
        pip_install_cmd = [
            self.venv_bin(filename="python"),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-cache-dir",
        ]

        self._install_latest_requirements(pip_install_cmd)

    def _install_latest_requirements(self, pip_install_cmd):
        """Install all the latest core requirements."""
        # First, upgrade pip and setuptools to their latest versions
        cmd = pip_install_cmd + ["pip", "setuptools"]
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path,
        )

        # Nothing else to install for generic projects.
        if self.config.doctype == GENERIC:
            return

        # Second, install all the latest core requirements
        requirements = []

        if self.config.doctype == "mkdocs":
            requirements.append("mkdocs")
        else:
            requirements.append("sphinx")

        cmd = copy.copy(pip_install_cmd)
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path,
        )

    def install_requirements_file(self, install):
        """
        Install a requirements file using pip.

        :param install: A install object from the config module.
        :type install: readthedocs.config.models.PythonInstallRequirements
        """
        requirements_file_path = install.requirements
        if requirements_file_path:
            args = [
                self.venv_bin(filename="python"),
                "-m",
                "pip",
                "install",
            ]
            if self.project.has_feature(Feature.PIP_ALWAYS_UPGRADE):
                args += ["--upgrade"]
            args += [
                "--exists-action=w",
                "--no-cache-dir",
                "-r",
                requirements_file_path,
            ]
            self.build_env.run(
                *args,
                cwd=self.checkout_path,
                bin_path=self.venv_bin(),
            )


class Conda(PythonEnvironment):
    """
    A Conda_ environment.

    .. _Conda: https://conda.io/docs/
    """

    # pylint: disable=arguments-differ
    def venv_bin(self, filename=None):
        prefixes = ["$CONDA_ENVS_PATH", "$CONDA_DEFAULT_ENV", "bin"]
        return super().venv_bin(prefixes, filename=filename)

    def conda_bin_name(self):
        """
        Decide whether use ``mamba`` or ``conda`` to create the environment.

        ``mamba`` is really fast to solve dependencies and download channel
        metadata on startup.

        See https://github.com/QuantStack/mamba
        """
        return self.config.python_interpreter

    def setup_base(self):
        self._append_core_requirements()
        self._show_environment_yaml()

        self.build_env.run(
            self.conda_bin_name(),
            "env",
            "create",
            "--quiet",
            "--name",
            self.version.slug,
            "--file",
            self.config.conda.environment,
            bin_path=None,  # Don't use conda bin that doesn't exist yet
            cwd=self.checkout_path,
        )

    def _show_environment_yaml(self):
        """Show ``environment.yml`` file in the Build output."""
        self.build_env.run(
            "cat",
            self.config.conda.environment,
            cwd=self.checkout_path,
        )

    def _append_core_requirements(self):
        """
        Append Read the Docs dependencies to Conda environment file.

        This help users to pin their dependencies properly without us upgrading
        them in the second ``conda install`` run.

        See https://github.com/readthedocs/readthedocs.org/pull/5631
        """
        try:
            # Allow symlinks, but only the ones that resolve inside the base directory.
            inputfile = safe_open(
                os.path.join(
                    self.checkout_path,
                    self.config.conda.environment,
                ),
                "r",
                allow_symlinks=True,
                base_path=self.checkout_path,
            )
            if not inputfile:
                raise UserFileNotFound(
                    message_id=UserFileNotFound.FILE_NOT_FOUND,
                    format_values={
                        "filename": self.config.conda.environment,
                    },
                )
            environment = parse_yaml(inputfile)
        except IOError:
            log.warning(
                "There was an error while reading Conda environment file.",
            )
        except ParseError:
            log.warning(
                "There was an error while parsing Conda environment file.",
            )
        else:
            # Append conda dependencies directly to ``dependencies`` and pip
            # dependencies to ``dependencies.pip``
            pip_requirements, conda_requirements = self._get_core_requirements()
            dependencies = environment.get("dependencies", [])
            pip_dependencies = {"pip": pip_requirements}

            for item in dependencies:
                if isinstance(item, dict) and "pip" in item:
                    # NOTE: pip can be ``None``
                    pip_requirements.extend(item.get("pip") or [])
                    dependencies.remove(item)
                    break

            dependencies.append(pip_dependencies)
            dependencies.extend(conda_requirements)
            environment.update({"dependencies": dependencies})
            try:
                # Allow symlinks, but only the ones that resolve inside the base directory.
                outputfile = safe_open(
                    os.path.join(
                        self.checkout_path,
                        self.config.conda.environment,
                    ),
                    "w",
                    allow_symlinks=True,
                    base_path=self.checkout_path,
                )
                if not outputfile:
                    raise UserFileNotFound(
                        message_id=UserFileNotFound.FILE_NOT_FOUND,
                        format_values={
                            "filename": self.config.conda.environment,
                        },
                    )
                yaml.safe_dump(environment, outputfile)
            except IOError:
                log.warning(
                    "There was an error while writing the new Conda environment file.",
                )

    def _get_core_requirements(self):
        # Use conda for requirements it packages
        conda_requirements = []

        # Install pip-only things.
        pip_requirements = []

        if self.config.doctype == "mkdocs":
            pip_requirements.append("mkdocs")
        else:
            conda_requirements.extend(["sphinx"])

        return pip_requirements, conda_requirements

    def install_core_requirements(self):
        """
        Skip installing requirements.

        Skip installing core requirements, since they were already appended to
        the user's ``environment.yml`` and installed at ``conda env create`` step.
        """

    def install_requirements_file(self, install):
        # as the conda environment was created by using the ``environment.yml``
        # defined by the user, there is nothing to update at this point
        pass
