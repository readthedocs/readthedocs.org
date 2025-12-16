"""
The ``director`` module can be seen as the entrypoint of the build process.

It "directs" all of the high-level build jobs:

* checking out the repo
* setting up the environment
* fetching instructions etc.
"""

import datetime
import os
import tarfile

import structlog
import yaml
from django.conf import settings

from readthedocs.builds.constants import EXTERNAL
from readthedocs.config.config import CONFIG_FILENAME_REGEX
from readthedocs.config.find import find_one
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.core.utils.objects import get_dotted_attribute
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda
from readthedocs.doc_builder.python_environments import Virtualenv
from readthedocs.projects.constants import BUILD_COMMANDS_OUTPUT_PATH_HTML
from readthedocs.projects.constants import GENERIC
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.notifications import MESSAGE_PROJECT_SSH_KEY_WITH_WRITE_ACCESS
from readthedocs.projects.signals import after_build
from readthedocs.projects.signals import before_build
from readthedocs.projects.signals import before_vcs
from readthedocs.projects.tasks.storage import StorageType
from readthedocs.projects.tasks.storage import get_storage


log = structlog.get_logger(__name__)


class BuildDirector:
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

    def setup_vcs(self):
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
            raise RepositoryError(RepositoryError.UNSUPPORTED_VCS)

        before_vcs.send(
            sender=self.data.version,
            environment=self.vcs_environment,
        )

        # Create the VCS repository where all the commands are going to be
        # executed for a particular VCS type
        self.vcs_repository = self.data.project.vcs_repo(
            version=self.data.version,
            environment=self.vcs_environment,
        )

        # We can't do too much on ``pre_checkout`` because we haven't
        # cloned the repository yet and we don't know what the user wrote
        # in the `.readthedocs.yaml` yet.
        #
        # We could implement something different in the future if we download
        # the `.readthedocs.yaml` file without cloning.
        # See https://github.com/readthedocs/readthedocs.org/issues/8935
        #
        # self.run_build_job("pre_checkout")
        self.checkout()

        self.run_build_job("post_checkout")

        commit = self.data.build_commit or self.vcs_repository.commit
        if commit:
            self.data.build["commit"] = commit

    def create_vcs_environment(self):
        self.vcs_environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            build=self.data.build,
            environment=self.get_vcs_env_vars(),
            container_image=settings.RTD_DOCKER_CLONE_IMAGE,
            api_client=self.data.api_client,
        )

    def create_build_environment(self):
        self.build_environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            config=self.data.config,
            build=self.data.build,
            environment=self.get_build_env_vars(),
            api_client=self.data.api_client,
        )

    def setup_environment(self):
        """
        Create the environment and install required dependencies.

        1. install OS dependencies (apt)
        2. create language (e.g. Python) environment
        3. install dependencies into the environment
        """
        # Environment used for building code, usually with Docker
        language_environment_cls = Virtualenv
        if self.data.config.is_using_conda:
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

        self.run_build_job("pre_system_dependencies")
        self.system_dependencies()
        self.run_build_job("post_system_dependencies")

        # Install all ``build.tools`` specified by the user
        self.install_build_tools()

        self.run_build_job("pre_create_environment")
        self.create_environment()
        self.run_build_job("post_create_environment")

        self.run_build_job("pre_install")
        self.install()
        self.run_build_job("post_install")

    def build(self):
        """
        Build all the formats specified by the user.

        1. build HTML
        2. build HTMLZzip
        3. build PDF
        4. build ePub
        """
        self.run_build_job("pre_build")

        # Build all formats
        self.build_html()
        self.build_htmlzip()
        self.build_pdf()
        self.build_epub()

        self.run_build_job("post_build")
        self.store_readthedocs_build_yaml()

        after_build.send(
            sender=self.data.version,
        )

    # VCS checkout
    def checkout(self):
        """Checkout Git repo and load build config file."""

        log.info("Cloning and fetching.")
        self.vcs_repository.update()

        # Check if the key has write access to the repository (RTD Business only).
        # This check is done immediately after clone step, and before running any
        # commands that make use of user given input (like the post_checkout job).
        has_ssh_key_with_write_access = False
        if settings.ALLOW_PRIVATE_REPOS:
            has_ssh_key_with_write_access = self.vcs_repository.has_ssh_key_with_write_access()
            if has_ssh_key_with_write_access != self.data.project.has_ssh_key_with_write_access:
                self.data.api_client.project(self.data.project.pk).patch(
                    {"has_ssh_key_with_write_access": has_ssh_key_with_write_access}
                )

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            hard_failure = now >= datetime.datetime(
                2025, 12, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            )
            if has_ssh_key_with_write_access:
                if hard_failure and settings.RTD_ENFORCE_BROWNOUTS_FOR_DEPRECATIONS:
                    raise BuildUserError(BuildUserError.SSH_KEY_WITH_WRITE_ACCESS)
                else:
                    self.attach_notification(
                        attached_to=f"project/{self.data.project.pk}",
                        message_id=MESSAGE_PROJECT_SSH_KEY_WITH_WRITE_ACCESS,
                        dismissable=True,
                    )

        # Get the default branch of the repository if the project doesn't
        # have an explicit default branch set and we are building latest.
        # The identifier from latest will be updated with this value
        # if the build succeeds.
        is_latest_without_default_branch = (
            self.data.version.is_machine_latest and not self.data.project.default_branch
        )
        if is_latest_without_default_branch:
            self.data.default_branch = self.data.build_director.vcs_repository.get_default_branch()
            log.info(
                "Default branch for the repository detected.",
                default_branch=self.data.default_branch,
            )

        # We can skip the checkout step since we just cloned the repository,
        # and the default branch is already checked out.
        if not is_latest_without_default_branch:
            identifier = self.data.build_commit or self.data.version.identifier
            log.info("Checking out.", identifier=identifier)
            self.vcs_repository.checkout(identifier)

        # The director is responsible for understanding which config file to use for a build.
        # In order to reproduce a build 1:1, we may use readthedocs_yaml_path defined by the build
        # instead of per-version or per-project.
        # Use the below line to fetch the readthedocs_yaml_path defined per-build.
        # custom_config_file = self.data.build.get("readthedocs_yaml_path", None)
        custom_config_file = None

        # This logic can be extended with version-specific config files
        if not custom_config_file and self.data.version.project.readthedocs_yaml_path:
            custom_config_file = self.data.version.project.readthedocs_yaml_path

        if custom_config_file:
            log.info("Using a custom .readthedocs.yaml file.", path=custom_config_file)

        checkout_path = self.data.project.checkout_path(self.data.version.slug)
        default_config_file = find_one(checkout_path, CONFIG_FILENAME_REGEX)
        final_config_file = custom_config_file or default_config_file

        # Output the path for the config file used.
        # This works as confirmation for us & the user about which file is used,
        # as well as the fact that *any* config file is used.
        if final_config_file:
            self.vcs_environment.run(
                "cat",
                # Show user the relative path to the config file
                # TODO: Have our standard path replacement code catch this.
                # https://github.com/readthedocs/readthedocs.org/pull/10413#discussion_r1230765843
                final_config_file.replace(checkout_path + "/", ""),
                cwd=checkout_path,
            )

        self.data.config = load_yaml_config(
            version=self.data.version,
            readthedocs_yaml_path=custom_config_file,
        )
        self.data.build["config"] = self.data.config.as_dict()
        self.data.build["readthedocs_yaml_path"] = custom_config_file

        # Raise a build error if the project is not using a config file or using v1
        if self.data.config.version not in ("2", 2):
            raise BuildUserError(BuildUserError.NO_CONFIG_FILE_DEPRECATED)

        # Raise a build error if the project is using "build.image" on their config file
        build_config_key = self.data.config.source_config.get("build", {})
        if "image" in build_config_key:
            raise BuildUserError(BuildUserError.BUILD_IMAGE_CONFIG_KEY_DEPRECATED)

        # TODO: move this validation to the Config object once we are settled here
        if "image" not in build_config_key and "os" not in build_config_key:
            raise BuildUserError(BuildUserError.BUILD_OS_REQUIRED)

        self.vcs_repository.update_submodules(self.data.config)

        # If the config has a post_checkout job, we stop the build,
        # as it could be abused to write to the repository.
        if has_ssh_key_with_write_access and get_dotted_attribute(
            self.data.config, "build.jobs.post_checkout", None
        ):
            raise BuildUserError(BuildUserError.SSH_KEY_WITH_WRITE_ACCESS)

    # System dependencies (``build.apt_packages``)
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

    # Language environment
    def create_environment(self):
        if self.data.config.build.jobs.create_environment is not None:
            self.run_build_job("create_environment")
            return

        # If the builder is generic, we have nothing to do here,
        # as the commnads are provided by the user.
        if self.data.config.doctype == GENERIC:
            return

        self.language_environment.setup_base()

    # Install
    def install(self):
        if self.data.config.build.jobs.install is not None:
            self.run_build_job("install")
            return

        # If the builder is generic, we have nothing to do here,
        # as the commnads are provided by the user.
        if self.data.config.doctype == GENERIC:
            return

        self.language_environment.install_core_requirements()
        self.language_environment.install_requirements()

    # Build
    def build_html(self):
        if self.data.config.build.jobs.build.html is not None:
            self.run_build_job("build.html")
            return
        return self.build_docs_class(self.data.config.doctype)

    def build_pdf(self):
        if "pdf" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

        if self.data.config.build.jobs.build.pdf is not None:
            self.run_build_job("build.pdf")
            return

        # Mkdocs has no pdf generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_pdf")

        return False

    def build_htmlzip(self):
        if "htmlzip" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

        if self.data.config.build.jobs.build.htmlzip is not None:
            self.run_build_job("build.htmlzip")
            return

        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_singlehtmllocalmedia")
        return False

    def build_epub(self):
        if "epub" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

        if self.data.config.build.jobs.build.epub is not None:
            self.run_build_job("build.epub")
            return

        # Mkdocs has no epub generation currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_epub")
        return False

    def run_build_job(self, job):
        """
        Run a command specified by the user under `build.jobs.` config key.

        It uses the "VCS environment" for pre_/post_ checkout jobs and "build
        environment" for the rest of them.

        Note that user's commands:

        - are not escaped
        - are run with under the path where the repository was cloned
        - are run as RTD_DOCKER_USER user
        - users can't run commands as `root` user
        - all the user's commands receive same environment variables as regular commands

        Example:

          build:
            jobs:
              pre_install:
                - echo `date`
                - python path/to/myscript.py
              pre_build:
                - sed -i **/*.rst -e "s|{version}|v3.5.1|g"
              build:
                html:
                  - make html
                pdf:
                  - make pdf

        In this case, `self.data.config.build.jobs.pre_build` will contains
        `sed` command.
        """
        commands = get_dotted_attribute(self.data.config, f"build.jobs.{job}", None)
        if not commands:
            return

        cwd = self.data.project.checkout_path(self.data.version.slug)
        environment = self.vcs_environment
        if job not in ("pre_checkout", "post_checkout"):
            environment = self.build_environment

        for command in commands:
            environment.run(command, escape_command=False, cwd=cwd)

    def check_old_output_directory(self):
        """
        Check if there the directory '_build/html' exists and fail the build if so.

        Read the Docs used to build artifacts into '_build/html' and there are
        some projects with this path hardcoded in their files. Those builds are
        having unexpected behavior since we are not using that path anymore.

        In case we detect they are keep using that path, we fail the build
        explaining this.
        """
        command = self.build_environment.run(
            "test",
            "-x",
            "_build/html",
            cwd=self.data.project.checkout_path(self.data.version.slug),
            record=False,
        )
        if command.exit_code == 0:
            log.warning("Directory '_build/html' exists. This may lead to unexpected behavior.")
            raise BuildUserError(BuildUserError.BUILD_OUTPUT_OLD_DIRECTORY_USED)

    def run_build_commands(self):
        """Runs each build command in the build environment."""

        python_reshim_commands = (
            {"pip", "install"},
            {"conda", "create"},
            {"conda", "install"},
            {"mamba", "create"},
            {"mamba", "install"},
            {"poetry", "install"},
        )
        rust_reshim_commands = ({"cargo", "install"},)

        cwd = self.data.project.checkout_path(self.data.version.slug)
        environment = self.build_environment
        for command in self.data.config.build.commands:
            environment.run(command, escape_command=False, cwd=cwd)

            # Execute ``asdf reshim python`` if the user is installing a
            # package since the package may contain an executable
            # See https://github.com/readthedocs/readthedocs.org/pull/9150#discussion_r882849790
            for python_reshim_command in python_reshim_commands:
                # Convert tuple/list into set to check reshim command is a
                # subset of the command itself. This is to find ``pip install``
                # but also ``pip -v install`` and ``python -m pip install``
                if python_reshim_command.issubset(command.split()):
                    environment.run(
                        *["asdf", "reshim", "python"],
                        escape_command=False,
                        cwd=cwd,
                        record=False,
                    )

            # Do same for Rust
            for rust_reshim_command in rust_reshim_commands:
                if rust_reshim_command.issubset(command.split()):
                    environment.run(
                        *["asdf", "reshim", "rust"],
                        escape_command=False,
                        cwd=cwd,
                        record=False,
                    )

        html_output_path = os.path.join(cwd, BUILD_COMMANDS_OUTPUT_PATH_HTML)
        if not os.path.exists(html_output_path):
            raise BuildUserError(BuildUserError.BUILD_COMMANDS_WITHOUT_OUTPUT)

        # Update the `Version.documentation_type` to match the doctype defined
        # by the config file. When using `build.commands` it will be `GENERIC`
        self.data.version.documentation_type = self.data.config.doctype

        self.store_readthedocs_build_yaml()

    def install_build_tools(self):
        """
        Install all ``build.tools`` defined by the user in the config file.

        It uses ``asdf`` behind the scenes to manage all the tools and versions
        of them. These tools/versions are stored in the Cloud cache and are
        downloaded on each build (~50 - ~100Mb).

        If the requested tool/version is not present in the cache, it's
        installed via ``asdf`` on the fly.
        """
        if settings.RTD_DOCKER_COMPOSE:
            # Create a symlink for ``root`` user to use the same ``.asdf``
            # installation as the ``docs`` user. Required for local building
            # since everything is run as ``root`` when using Local Development
            # instance
            cmd = [
                "ln",
                "-s",
                os.path.join(settings.RTD_DOCKER_WORKDIR, ".asdf"),
                "/root/.asdf",
            ]
            self.build_environment.run(
                *cmd,
                record=False,
            )

        build_tools_storage = get_storage(
            project=self.data.project,
            build_id=self.data.build["id"],
            api_client=self.data.api_client,
            storage_type=StorageType.build_tools,
        )

        for tool, version in self.data.config.build.tools.items():
            full_version = version.full_version  # e.g. 3.9 -> 3.9.7

            # TODO: generate the correct path for the Python version
            # see https://github.com/readthedocs/readthedocs.org/pull/8447#issuecomment-911562267
            # tool_path = f'{self.config.build.os}/{tool}/2021-08-30/{full_version}.tar.gz'

            build_os = self.data.config.build.os
            if build_os == "ubuntu-lts-latest":
                _, build_os = settings.RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-lts-latest"].split(
                    ":"
                )

            tool_path = f"{build_os}-{tool}-{full_version}.tar.gz"
            tool_version_cached = build_tools_storage.exists(tool_path)
            if tool_version_cached:
                remote_fd = build_tools_storage.open(tool_path, mode="rb")
                with tarfile.open(fileobj=remote_fd) as tar:
                    # Extract it on the shared path between host and Docker container
                    extract_path = os.path.join(self.data.project.doc_path, "tools")
                    tar.extractall(extract_path)

                    # Move the extracted content to the ``asdf`` installation
                    cmd = [
                        "mv",
                        f"{extract_path}/{full_version}",
                        os.path.join(
                            settings.RTD_DOCKER_WORKDIR,
                            f".asdf/installs/{tool}/{full_version}",
                        ),
                    ]
                    self.build_environment.run(
                        *cmd,
                        record=False,
                    )
            else:
                log.debug(
                    "Cached version for tool not found.",
                    os=self.data.config.build.os,
                    tool=tool,
                    full_version=full_version,
                    tool_path=tool_path,
                )
                # If the tool version selected is not available from the
                # cache we compile it at build time
                cmd = [
                    # TODO: make ``PYTHON_CONFIGURE_OPTS="--enable-shared"``
                    # environment variable to work here. Note that
                    # ``self.build_environment.run`` does not support passing
                    # environment for a particular command:
                    # https://github.com/readthedocs/readthedocs.org/blob/9d2d1a2/readthedocs/doc_builder/environments.py#L430-L431
                    "asdf",
                    "install",
                    tool,
                    full_version,
                ]
                self.build_environment.run(
                    *cmd,
                )

            # Make the tool version chosen by the user the default one
            cmd = [
                "asdf",
                "global",
                tool,
                full_version,
            ]
            self.build_environment.run(
                *cmd,
            )

            # Recreate shims for this tool to make the new version
            # installed available
            # https://asdf-vm.com/learn-more/faq.html#newly-installed-exectable-not-running
            cmd = [
                "asdf",
                "reshim",
                tool,
            ]
            self.build_environment.run(
                *cmd,
                record=False,
            )

            if all(
                [
                    tool == "python",
                    # Do not install them if the tool version was cached
                    # because these dependencies are already installed when
                    # created with our script and uploaded to the cache's
                    # bucket
                    not tool_version_cached,
                    # Do not install them on conda/mamba since they are not
                    # needed because the environment is managed by conda/mamba
                    # itself
                    self.data.config.python_interpreter not in ("conda", "mamba"),
                ]
            ):
                # We cap setuptools to avoid breakage of projects
                # relying on setup.py invokations,
                # see https://github.com/readthedocs/readthedocs.org/issues/8659
                setuptools_version = (
                    "setuptools<58.3.0"
                    if self.data.config.is_using_setup_py_install
                    else "setuptools"
                )
                # Install our own requirements if the version is compiled
                cmd = [
                    "python",
                    "-mpip",
                    "install",
                    "-U",
                    "virtualenv",
                    setuptools_version,
                ]
                self.build_environment.run(
                    *cmd,
                )

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
        # If the builder is generic, we have nothing to do here,
        # as the commnads are provided by the user.
        if builder_class == GENERIC:
            return

        builder = get_builder_class(builder_class)(
            build_env=self.build_environment,
            python_env=self.language_environment,
        )

        if builder_class == self.data.config.doctype:
            builder.show_conf()
            self.data.version.documentation_type = builder.get_final_doctype()

        success = builder.build()
        return success

    def get_vcs_env_vars(self):
        """Get environment variables to be included in the VCS setup step."""
        env = self.get_rtd_env_vars()
        # Don't prompt for username, this requires Git 2.3+
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["READTHEDOCS_GIT_CLONE_TOKEN"] = self.data.project.clone_token
        return env

    def get_rtd_env_vars(self):
        """Get bash environment variables specific to Read the Docs."""
        env = {
            "READTHEDOCS": "True",
            "READTHEDOCS_VERSION": self.data.version.slug,
            "READTHEDOCS_VERSION_TYPE": self.data.version.type,
            "READTHEDOCS_VERSION_NAME": self.data.version.verbose_name,
            "READTHEDOCS_PROJECT": self.data.project.slug,
            "READTHEDOCS_LANGUAGE": self.data.project.language,
            "READTHEDOCS_REPOSITORY_PATH": self.data.project.checkout_path(self.data.version.slug),
            "READTHEDOCS_OUTPUT": os.path.join(
                self.data.project.checkout_path(self.data.version.slug), "_readthedocs/"
            ),
            "READTHEDOCS_GIT_CLONE_URL": self.data.project.repo,
            # TODO: we don't have access to the database from the builder.
            # We need to find a way to expose HTML_URL here as well.
            # "READTHEDOCS_GIT_HTML_URL": self.data.project.remote_repository.html_url,
            "READTHEDOCS_GIT_IDENTIFIER": self.data.version.git_identifier,
            "READTHEDOCS_GIT_COMMIT_HASH": self.data.build["commit"],
            "READTHEDOCS_PRODUCTION_DOMAIN": settings.PRODUCTION_DOMAIN,
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
                    # NOTE: should these be prefixed with "READTHEDOCS_"?
                    "CONDA_ENVS_PATH": os.path.join(self.data.project.doc_path, "conda"),
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
                    "READTHEDOCS_VIRTUALENV_PATH": os.path.join(
                        self.data.project.doc_path, "envs", self.data.version.slug
                    ),
                }
            )

        env.update(
            {
                "READTHEDOCS_CANONICAL_URL": self.data.version.canonical_url,
            }
        )

        # Update environment from Project's specific environment variables,
        # avoiding to expose private environment variables
        # if the version is external (i.e. a PR build).
        env.update(
            self.data.project.environment_variables(public_only=self.data.version.is_external)
        )

        return env

    def is_type_sphinx(self):
        """Is documentation type Sphinx."""
        return "sphinx" in self.data.config.doctype

    def store_readthedocs_build_yaml(self):
        # load YAML from user
        yaml_path = os.path.join(
            self.data.project.artifact_path(version=self.data.version.slug, type_="html"),
            "readthedocs-build.yaml",
        )

        if not os.path.exists(yaml_path):
            log.debug("Build output YAML file (readtehdocs-build.yaml) does not exist.")
            return

        try:
            with safe_open(yaml_path, "r") as f:
                data = yaml.safe_load(f)
        except Exception:
            # NOTE: skip this work for now until we decide whether or not this
            # YAML file is required.
            #
            # NOTE: decide whether or not we want this
            # file to be mandatory and raise an exception here.
            return

        log.info("readthedocs-build.yaml loaded.", path=yaml_path)

        # TODO: validate the YAML generated by the user
        # self._validate_readthedocs_build_yaml(data)

        # Copy the YAML data into `Version.build_data`.
        # It will be saved when the API is hit.
        # This data will be used by the `/_/readthedocs-config.json` API endpoint.
        self.data.version.build_data = data

    def attach_notification(
        self,
        attached_to,
        message_id,
        format_values=None,
        state="unread",
        dismissable=False,
        news=False,
    ):
        """
        Attach a notification to build in progress using the APIv2.

        :param attached_to: The object to which the notification is attached.
         It should have the form of `project/{project_id}` or `build/{build_id}`.
        """

        format_values = format_values or {}
        # NOTE: we are using APIv2 here because it uses BuildAPIKey authentication,
        # which is not currently supported by APIv3.
        self.data.api_client.notifications.post(
            {
                "attached_to": attached_to,
                "message_id": message_id,
                "state": state,  # Optional
                "dismissable": dismissable,
                "news": news,
                "format_values": format_values,
            }
        )
