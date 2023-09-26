"""An abstraction over virtualenv and Conda environments."""

import copy
import itertools
import os

import structlog
import yaml

from readthedocs.config import PIP, SETUPTOOLS, ParseError
from readthedocs.config import parse as parse_yaml
from readthedocs.config.models import PythonInstall, PythonInstallRequirements
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.loader import get_builder_class
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
        log.bind(
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
            local_path = (
                os.path.join('.', install.path) if install.path != '.' else install.path
            )
            extra_req_param = ''
            if install.extra_requirements:
                extra_req_param = '[{}]'.format(
                    ','.join(install.extra_requirements)
                )
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
                self.venv_bin(filename='python'),
                os.path.join(install.path, 'setup.py'),
                'install',
                '--force',
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
            '-mvirtualenv',
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
            self.venv_bin(filename='python'),
            '-m',
            'pip',
            'install',
            '--upgrade',
            '--no-cache-dir',
        ]

        if self.project.has_feature(Feature.INSTALL_LATEST_CORE_REQUIREMENTS):
            self._install_latest_requirements(pip_install_cmd)
        else:
            self._install_old_requirements(pip_install_cmd)

    def _install_latest_requirements(self, pip_install_cmd):
        """
        Install all the latest core requirements.

        By enabling the feature flag ``INSTALL_LATEST_CORE_REQUIREMENTS``
        projects will automatically get installed all the latest core
        requirements: pip, setuptools, sphinx, readthedocs-sphinx-ext and mkdocs.

        This is the new behavior and where we are moving towards.
        """
        # First, upgrade pip and setuptools to their latest versions
        cmd = pip_install_cmd + ["pip", "setuptools"]
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path,
        )

        # Second, install all the latest core requirements
        requirements = []

        if self.config.doctype == "mkdocs":
            requirements.append("mkdocs")
        else:
            requirements.extend(
                [
                    "sphinx",
                    "readthedocs-sphinx-ext",
                ]
            )

        cmd = copy.copy(pip_install_cmd)
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path,
        )

    def _install_old_requirements(self, pip_install_cmd):
        """
        Install old core requirements.

        There are bunch of feature flags that will be taken in consideration to
        decide whether or not upgrade some of the core dependencies to their
        latest versions.

        This is the old behavior and the one we want to get rid off.
        """
        # Install latest pip and setuptools first,
        # so it is used when installing the other requirements.
        pip_version = self.project.get_feature_value(
            Feature.DONT_INSTALL_LATEST_PIP,
            # 20.3 uses the new resolver by default.
            positive='pip<20.3',
            negative='pip',
        )
        # Installing a project with setup.py install is deprecated
        # in new versions of setuptools, so we need to pin setuptools
        # to a supported version if the project is using setup.py install.
        setuptools_version = (
            "setuptools<58.3.0"
            if self.config.is_using_setup_py_install
            else "setuptools"
        )
        cmd = pip_install_cmd + [pip_version, setuptools_version]
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path,
        )

        requirements = []

        # Unpin Pillow on newer Python versions to avoid re-compiling
        # https://pillow.readthedocs.io/en/stable/installation.html#python-support
        if self.config.python.version in ("2.7", "3.4", "3.5", "3.6", "3.7"):
            requirements.append("pillow==5.4.1")
        else:
            requirements.append("pillow")

        requirements.extend(
            [
                "mock==1.0.1",
                "alabaster>=0.7,<0.8,!=0.7.5",
                "commonmark==0.9.1",
                "recommonmark==0.5.0",
            ]
        )

        if self.config.doctype == 'mkdocs':
            requirements.append("mkdocs")
        else:
            requirements.extend(
                [
                    "sphinx",
                    "sphinx-rtd-theme",
                    self.project.get_feature_value(
                        Feature.USE_SPHINX_RTD_EXT_LATEST,
                        positive="readthedocs-sphinx-ext",
                        negative="readthedocs-sphinx-ext<2.3",
                    ),
                ]
            )

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
        if requirements_file_path is None:
            # This only happens when the config file is from v1.
            # We try to find a requirements file.
            builder_class = get_builder_class(self.config.doctype)
            docs_dir = (
                builder_class(
                    build_env=self.build_env,
                    python_env=self,
                ).docs_dir()
            )
            paths = [docs_dir, '']
            req_files = ['pip_requirements.txt', 'requirements.txt']
            for path, req_file in itertools.product(paths, req_files):
                test_path = os.path.join(self.checkout_path, path, req_file)
                if os.path.exists(test_path):
                    requirements_file_path = os.path.relpath(
                        test_path,
                        self.checkout_path,
                    )
                    break

        if requirements_file_path:
            args = [
                self.venv_bin(filename='python'),
                '-m',
                'pip',
                'install',
            ]
            if self.project.has_feature(Feature.PIP_ALWAYS_UPGRADE):
                args += ['--upgrade']
            args += [
                '--exists-action=w',
                '--no-cache-dir',
                '-r',
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
        # Config file using ``build.tools.python``
        if self.config.using_build_tools:
            return self.config.python_interpreter
        return 'conda'

    def setup_base(self):
        if self.project.has_feature(Feature.CONDA_APPEND_CORE_REQUIREMENTS):
            self._append_core_requirements()
            self._show_environment_yaml()

        self.build_env.run(
            self.conda_bin_name(),
            'env',
            'create',
            '--quiet',
            '--name',
            self.version.slug,
            '--file',
            self.config.conda.environment,
            bin_path=None,  # Don't use conda bin that doesn't exist yet
            cwd=self.checkout_path,
        )

    def _show_environment_yaml(self):
        """Show ``environment.yml`` file in the Build output."""
        self.build_env.run(
            'cat',
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
                    UserFileNotFound.FILE_NOT_FOUND.format(
                        self.config.conda.environment
                    )
                )
            environment = parse_yaml(inputfile)
        except IOError:
            log.warning(
                'There was an error while reading Conda environment file.',
            )
        except ParseError:
            log.warning(
                'There was an error while parsing Conda environment file.',
            )
        else:
            # Append conda dependencies directly to ``dependencies`` and pip
            # dependencies to ``dependencies.pip``
            if self.project.has_feature(Feature.INSTALL_LATEST_CORE_REQUIREMENTS):
                pip_requirements, conda_requirements = self._get_new_core_requirements()
            else:
                pip_requirements, conda_requirements = self._get_old_core_requirements()
            dependencies = environment.get('dependencies', [])
            pip_dependencies = {'pip': pip_requirements}

            for item in dependencies:
                if isinstance(item, dict) and 'pip' in item:
                    # NOTE: pip can be ``None``
                    pip_requirements.extend(item.get('pip') or [])
                    dependencies.remove(item)
                    break

            dependencies.append(pip_dependencies)
            dependencies.extend(conda_requirements)
            environment.update({'dependencies': dependencies})
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
                        UserFileNotFound.FILE_NOT_FOUND.format(
                            self.config.conda.environment
                        )
                    )
                yaml.safe_dump(environment, outputfile)
            except IOError:
                log.warning(
                    'There was an error while writing the new Conda '
                    'environment file.',
                )

    def _get_new_core_requirements(self):
        # Use conda for requirements it packages
        conda_requirements = []

        # Install pip-only things.
        pip_requirements = []

        if self.config.doctype == "mkdocs":
            pip_requirements.append("mkdocs")
        else:
            pip_requirements.append("readthedocs-sphinx-ext")
            conda_requirements.extend(["sphinx"])

        return pip_requirements, conda_requirements

    def _get_old_core_requirements(self):
        # Use conda for requirements it packages
        conda_requirements = [
            'mock',
            'pillow',
        ]

        # Install pip-only things.
        pip_requirements = [
            'recommonmark',
        ]

        if self.config.doctype == 'mkdocs':
            pip_requirements.append('mkdocs')
        else:
            pip_requirements.append('readthedocs-sphinx-ext')
            conda_requirements.extend(['sphinx', 'sphinx_rtd_theme'])

        return pip_requirements, conda_requirements

    def install_core_requirements(self):
        """Install basic Read the Docs requirements into the Conda env."""

        if self.project.has_feature(Feature.CONDA_APPEND_CORE_REQUIREMENTS):
            # Skip install core requirements since they were already appended to
            # the user's ``environment.yml`` and installed at ``conda env
            # create`` step.
            return

        pip_requirements, conda_requirements = self._get_old_core_requirements()
        # Install requirements via ``conda install`` command if they were
        # not appended to the ``environment.yml`` file.
        cmd = [
            self.conda_bin_name(),
            'install',
            '--yes',
            '--quiet',
            '--name',
            self.version.slug,
        ]
        cmd.extend(conda_requirements)
        self.build_env.run(
            *cmd,
            cwd=self.checkout_path,
            # TODO: on tests I found that we are not passing ``bin_path`` here
            # for some reason.
        )

        # Install requirements via ``pip install``
        pip_cmd = [
            self.venv_bin(filename='python'),
            '-m',
            'pip',
            'install',
            '-U',
            '--no-cache-dir',
        ]
        pip_cmd.extend(pip_requirements)
        self.build_env.run(
            *pip_cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path  # noqa - no comma here in py27 :/
        )

    def install_requirements_file(self, install):
        # as the conda environment was created by using the ``environment.yml``
        # defined by the user, there is nothing to update at this point
        pass
