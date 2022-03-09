import os
from collections import defaultdict

import structlog
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import EXTERNAL
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Feature
from readthedocs.projects.signals import after_build, before_build, before_vcs

log = structlog.get_logger(__name__)


class DocumentationBuilder:

    """
    Encapsulates all the logic to perform a build for user's documentation.

    This class handles all the VCS commands, setup OS and language (e.g. only
    Python for now) environment (via virtualenv or conda), installs all the
    required basic and user packages, and finally execute the build commands
    (e.g. Sphinx or MkDocs) to generate the artifacts.

    Note that this class *is not* in charge of doing anything related to Read
    the Docs, the platform, itself. These include not updating the `Build`'s
    status, or uploading the artifacts to the storage, creating the search
    index, among others.
    """

    def __init__(self, data):
        """
        Initializer.

        :param data: object with all the data grabbed by Celery task in
        ``before_start`` and used as a way to share data with this class
        by-directionally.

        :type data: readthedocs.projects.tasks.builds.TaskData

        """
        self.data = data

    def vcs(self):
        """
        Perform all VCS related steps.

        1. clone the repository
        2. checkout specific commit/identifier
        3. load the config file
        4. checkout submodules
        """
        # Make dirs if it does not exist to clone the repository under it
        if not os.path.exists(self.data.project.doc_path):
            os.makedirs(self.data.project.doc_path)

        if not self.data.project.vcs_class():
            raise RepositoryError(
                _('Repository type "{repo_type}" unknown').format(
                    repo_type=self.data.project.repo_type,
                ),
            )

        environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            build=self.data.build,
            environment=self.get_vcs_env_vars(),
            # Force the ``container_image`` to use one that has the latest
            # ca-certificate package which is compatible with Lets Encrypt
            container_image=settings.RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-20.04"],
        )
        with environment:
            before_vcs.send(
                sender=self.data.version,
                environment=environment,
            )

            # Create the VCS repository where all the commands are going to be
            # executed for a particular VCS type
            self.vcs_repository = self.data.project.vcs_repo(
                version=self.data.version.slug,
                environment=environment,
                verbose_name=self.data.version.verbose_name,
                version_type=self.data.version.type,
            )

            self.pre_checkout()
            self.checkout()
            self.post_checkout()

            commit = self.data.build_commit or self.vcs_repository.commit
            if commit:
                self.data.build["commit"] = commit

    def setup_environment(self):
        """
        Create the environment and install required dependencies.

        1. install OS dependencies (apt)
        2. create language (e.g. Python) environment
        3. install dependencies into the environment
        """
        self.build_environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            config=self.data.config,
            build=self.data.build,
            environment=self.get_build_env_vars(),
        )

        # Environment used for building code, usually with Docker
        with self.build_environment:
            language_environment_cls = Virtualenv
            if any(
                [
                    self.data.config.conda is not None,
                    self.data.config.python_interpreter in ("conda", "mamba"),
                ]
            ):
                language_environment_cls = Conda

            self.language_environment = language_environment_cls(
                version=self.data.version,
                build_env=self.build_environment,
                config=self.data.config,
            )

            # TODO: check if `before_build` and `after_build` are still useful
            # (maybe in commercial?)
            #
            # I didn't find they are used anywhere, we should probably remove them
            before_build.send(
                sender=self.data.version,
                environment=self.build_environment,
            )

            self.pre_system_dependencies()
            self.system_dependencies()
            self.post_system_dependencies()

            # Install all ``build.tools`` specified by the user
            if self.data.config.using_build_tools:
                self.language_environment.install_build_tools()

            self.pre_create_environment()
            self.create_environment()
            self.post_create_environment()

            self.pre_install()
            self.install()
            self.post_install()

            # TODO: remove this and document how to do it on `build.jobs.post_install`
            if self.data.project.has_feature(Feature.LIST_PACKAGES_INSTALLED_ENV):
                self.language_environment.list_packages_installed()

    def build(self):
        """
        Build all the formats specified by the user.

        1. build HTML
        2. build HTMLZzip
        3. build PDF
        4. build ePub
        """
        with self.build_environment:
            self.data.outcomes = defaultdict(lambda: False)
            self.data.outcomes["html"] = self.build_html()
            self.data.outcomes["search"] = self.is_type_sphinx()
            self.data.outcomes["localmedia"] = self.build_htmlzip()
            self.data.outcomes["pdf"] = self.build_pdf()
            self.data.outcomes["epub"] = self.build_epub()

            after_build.send(
                sender=self.data.version,
            )

    # VCS checkout
    def pre_checkout(self):
        # We can't do too much here because we haven't cloned the repository
        # yet and we don't know what the user wrote in the `.readthedocs.yaml`
        # yet.
        #
        # We could implement something different in the future if we download
        # the `.readthedocs.yaml` file without cloning.
        # See https://github.com/readthedocs/readthedocs.org/issues/8935
        pass

    def checkout(self):
        log.info(
            "Clonning repository.",
        )
        self.vcs_repository.update()

        identifier = self.data.build_commit or self.data.version.identifier
        log.info("Checking out.", identifier=identifier)
        self.vcs_repository.checkout(identifier)

        self.data.config = load_yaml_config(version=self.data.version)
        self.data.build["config"] = self.data.config.as_dict()

        if self.vcs_repository.supports_submodules:
            self.vcs_repository.update_submodules(self.data.config)

    def post_checkout(self):
        commands = []  # self.data.config.build.jobs.post_checkout
        for command in commands:
            self.build_environment.run(command)

    # System dependencies (``build.apt_packages``)
    def pre_system_dependencies(self):
        commands = []  # self.data.config.build.jobs.pre_system_dependencies
        for command in commands:
            self.build_environment.run(command)

    # NOTE: `system_dependencies` should not be possible to override by the
    # user because it's executed as ``RTD_DOCKER_USER`` (e.g. ``root``) user.
    def system_dependencies(self):
        """
        Install apt packages from the config file.

        We don't allow to pass custom options or install from a path.
        The packages names are already validated when reading the config file.

        .. note::

           ``--quiet`` won't suppress the output,
           it would just remove the progress bar.
        """
        packages = self.data.config.build.apt_packages
        if packages:
            self.build_environment.run(
                "apt-get",
                "update",
                "--assume-yes",
                "--quiet",
                user=settings.RTD_DOCKER_SUPER_USER,
            )

            # put ``--`` to end all command arguments.
            self.build_environment.run(
                "apt-get",
                "install",
                "--assume-yes",
                "--quiet",
                "--",
                *packages,
                user=settings.RTD_DOCKER_SUPER_USER,
            )

    def post_system_dependencies(self):
        pass

    # Language environment
    def pre_create_environment(self):
        commands = []  # self.data.config.build.jobs.pre_create_environment
        for command in commands:
            self.build_environment.run(command)

    def create_environment(self):
        commands = []  # self.data.config.build.jobs.create_environment
        for command in commands:
            self.build_environment.run(command)

        if not commands:
            self.language_environment.setup_base()

    def post_create_environment(self):
        commands = []  # self.data.config.build.jobs.post_create_environment
        for command in commands:
            self.build_environment.run(command)

    # Install
    def pre_install(self):
        commands = []  # self.data.config.build.jobs.pre_install
        for command in commands:
            self.build_environment.run(command)

    def install(self):
        commands = []  # self.data.config.build.jobs.install
        for command in commands:
            self.build_environment.run(command)

        if not commands:
            self.language_environment.install_core_requirements()
            self.language_environment.install_requirements()

    def post_install(self):
        commands = []  # self.data.config.build.jobs.post_install
        for command in commands:
            self.build_environment.run(command)

    # Build
    def pre_build(self):
        commands = []  # self.data.config.build.jobs.pre_build
        for command in commands:
            self.build_environment.run(command)

    def build_html(self):
        commands = []  # self.data.config.build.jobs.build.html
        if commands:
            for command in commands:
                self.build_environment.run(command)
            return True

        return self.build_docs_class(self.data.config.doctype)

    def build_pdf(self):
        if "pdf" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

        commands = []  # self.data.config.build.jobs.build.pdf
        if commands:
            for command in commands:
                self.build_environment.run(command)
            return True

        # Mkdocs has no pdf generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_pdf")

        return False

    def build_htmlzip(self):
        if (
            "htmlzip" not in self.data.config.formats
            or self.data.version.type == EXTERNAL
        ):
            return False

        commands = []  # self.data.config.build.jobs.build.htmlzip
        if commands:
            for command in commands:
                self.build_environment.run(command)
            return True

        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_singlehtmllocalmedia")
        return False

    def build_epub(self):
        if "epub" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

        commands = []  # self.data.config.build.jobs.build.epub
        if commands:
            for command in commands:
                self.build_environment.run(command)
            return True

        # Mkdocs has no epub generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_epub")
        return False

    def post_build(self):
        commands = []  # self.data.config.build.jobs.post_build
        for command in commands:
            self.build_environment.run(command)

    # Helpers
    #
    # TODO: move somewhere or change names to make them private or something to
    # easily differentiate them from the normal flow.
    def build_docs_class(self, builder_class):
        """
        Build docs with additional doc backends.

        These steps are not necessarily required for the build to halt, so we
        only raise a warning exception here. A hard error will halt the build
        process.
        """
        builder = get_builder_class(builder_class)(
            build_env=self.build_environment,
            python_env=self.language_environment,
        )

        if builder_class == self.data.config.doctype:
            builder.append_conf()
            self.data.version.documentation_type = builder.get_final_doctype()

        success = builder.build()
        builder.move()

        return success

    def get_vcs_env_vars(self):
        """Get environment variables to be included in the VCS setup step."""
        env = self.get_rtd_env_vars()
        # Don't prompt for username, this requires Git 2.3+
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def get_rtd_env_vars(self):
        """Get bash environment variables specific to Read the Docs."""
        env = {
            "READTHEDOCS": "True",
            "READTHEDOCS_VERSION": self.data.version.slug,
            "READTHEDOCS_PROJECT": self.data.project.slug,
            "READTHEDOCS_LANGUAGE": self.data.project.language,
        }
        return env

    def get_build_env_vars(self):
        """Get bash environment variables used for all builder commands."""
        env = self.get_rtd_env_vars()

        # https://no-color.org/
        env["NO_COLOR"] = "1"

        if self.data.config.conda is not None:
            env.update(
                {
                    "CONDA_ENVS_PATH": os.path.join(
                        self.data.project.doc_path, "conda"
                    ),
                    "CONDA_DEFAULT_ENV": self.data.version.slug,
                    "BIN_PATH": os.path.join(
                        self.data.project.doc_path,
                        "conda",
                        self.data.version.slug,
                        "bin",
                    ),
                }
            )
        else:
            env.update(
                {
                    "BIN_PATH": os.path.join(
                        self.data.project.doc_path,
                        "envs",
                        self.data.version.slug,
                        "bin",
                    ),
                }
            )

        # Update environment from Project's specific environment variables,
        # avoiding to expose private environment variables
        # if the version is external (i.e. a PR build).
        env.update(
            self.data.project.environment_variables(
                public_only=self.data.version.is_external
            )
        )

        return env

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return "sphinx" in self.data.config.doctype
