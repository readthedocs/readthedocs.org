import os
import tarfile

import structlog
import yaml
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from readthedocs.builds.constants import EXTERNAL
from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.doc_builder.python_environments import Conda, Virtualenv
from readthedocs.projects.constants import BUILD_COMMANDS_OUTPUT_PATH_HTML
from readthedocs.projects.exceptions import RepositoryError
from readthedocs.projects.models import Feature
from readthedocs.projects.signals import after_build, before_build, before_vcs
from readthedocs.storage import build_tools_storage

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
            raise RepositoryError(
                _('Repository type "{repo_type}" unknown').format(
                    repo_type=self.data.project.repo_type,
                ),
            )

        before_vcs.send(
            sender=self.data.version,
            environment=self.vcs_environment,
        )

        # Create the VCS repository where all the commands are going to be
        # executed for a particular VCS type
        self.vcs_repository = self.data.project.vcs_repo(
            version=self.data.version.slug,
            environment=self.vcs_environment,
            verbose_name=self.data.version.verbose_name,
            version_type=self.data.version.type,
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
            # Force the ``container_image`` to use one that has the latest
            # ca-certificate package which is compatible with Lets Encrypt
            container_image=settings.RTD_DOCKER_BUILD_SETTINGS["os"]["ubuntu-20.04"],
        )

    def create_build_environment(self):
        use_gvisor = self.data.config.using_build_tools and self.data.config.build.jobs
        self.build_environment = self.data.environment_class(
            project=self.data.project,
            version=self.data.version,
            config=self.data.config,
            build=self.data.build,
            environment=self.get_build_env_vars(),
            use_gvisor=use_gvisor,
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
        if self.data.config.using_build_tools:
            self.install_build_tools()

        self.run_build_job("pre_create_environment")
        self.create_environment()
        self.run_build_job("post_create_environment")

        self.run_build_job("pre_install")
        self.install()
        self.run_build_job("post_install")

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

        self.run_build_job("pre_build")

        # Build all formats
        self.build_html()
        self.build_htmlzip()
        self.build_pdf()
        self.build_epub()

        self.run_build_job("post_build")
        self.generate_readthedocs_data_javascript()

        after_build.send(
            sender=self.data.version,
        )

    # VCS checkout
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
        self.language_environment.setup_base()

    # Install
    def install(self):
        self.language_environment.install_core_requirements()
        self.language_environment.install_requirements()

    # Build
    def build_html(self):
        return self.build_docs_class(self.data.config.doctype)

    def build_pdf(self):
        if "pdf" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

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

        # We don't generate a zip for mkdocs currently.
        if self.is_type_sphinx():
            return self.build_docs_class("sphinx_singlehtmllocalmedia")
        return False

    def build_epub(self):
        if "epub" not in self.data.config.formats or self.data.version.type == EXTERNAL:
            return False

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

        In this case, `self.data.config.build.jobs.pre_build` will contains
        `sed` command.
        """
        if (
            getattr(self.data.config.build, "jobs", None) is None
            or getattr(self.data.config.build.jobs, job, None) is None
        ):
            return

        cwd = self.data.project.checkout_path(self.data.version.slug)
        environment = self.vcs_environment
        if job not in ("pre_checkout", "post_checkout"):
            environment = self.build_environment

        commands = getattr(self.data.config.build.jobs, job, [])
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
            log.warning(
                "Directory '_build/html' exists. This may lead to unexpected behavior."
            )
            raise BuildUserError(BuildUserError.BUILD_OUTPUT_OLD_DIRECTORY_USED)

    def run_build_commands(self):
        reshim_commands = (
            {"pip", "install"},
            {"conda", "create"},
            {"conda", "install"},
            {"mamba", "create"},
            {"mamba", "install"},
            {"poetry", "install"},
        )
        cwd = self.data.project.checkout_path(self.data.version.slug)
        environment = self.build_environment
        for command in self.data.config.build.commands:
            environment.run(command, escape_command=False, cwd=cwd)

            # Execute ``asdf reshim python`` if the user is installing a
            # package since the package may contain an executable
            # See https://github.com/readthedocs/readthedocs.org/pull/9150#discussion_r882849790
            for reshim_command in reshim_commands:
                # Convert tuple/list into set to check reshim command is a
                # subset of the command itself. This is to find ``pip install``
                # but also ``pip -v install`` and ``python -m pip install``
                if reshim_command.issubset(command.split()):
                    environment.run(
                        *["asdf", "reshim", "python"],
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
        self.generate_readthedocs_data_javascript()

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

        for tool, version in self.data.config.build.tools.items():
            full_version = version.full_version  # e.g. 3.9 -> 3.9.7

            # TODO: generate the correct path for the Python version
            # see https://github.com/readthedocs/readthedocs.org/pull/8447#issuecomment-911562267
            # tool_path = f'{self.config.build.os}/{tool}/2021-08-30/{full_version}.tar.gz'
            tool_path = f"{self.data.config.build.os}-{tool}-{full_version}.tar.gz"
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
                # Install our own requirements if the version is compiled
                cmd = [
                    "python",
                    "-mpip",
                    "install",
                    "-U",
                    "virtualenv",
                    # We cap setuptools to avoid breakage of projects
                    # relying on setup.py invokations,
                    # see https://github.com/readthedocs/readthedocs.org/issues/8659
                    "setuptools<58.3.0",
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
        builder = get_builder_class(builder_class)(
            build_env=self.build_environment,
            python_env=self.language_environment,
        )

        if builder_class == self.data.config.doctype:
            builder.append_conf()
            self.data.version.documentation_type = builder.get_final_doctype()

        success = builder.build()
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
            "READTHEDOCS_VERSION_TYPE": self.data.version.type,
            "READTHEDOCS_VERSION_NAME": self.data.version.verbose_name,
            "READTHEDOCS_PROJECT": self.data.project.slug,
            "READTHEDOCS_LANGUAGE": self.data.project.language,
            "READTHEDOCS_OUTPUT": os.path.join(
                self.data.project.checkout_path(self.data.version.slug), "_readthedocs/"
            ),
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
                    "READTHEDOCS_VIRTUALENV_PATH": os.path.join(
                        self.data.project.doc_path, "envs", self.data.version.slug
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

    def generate_readthedocs_data_javascript(self):
        # load YAML from user
        yaml_path = os.path.join(
            self.data.project.artifact_path(
                version=self.data.version.slug, type_="html"
            ),
            "readthedocs-build.yaml",
        )

        try:
            log.warning(yaml_path)
            data = yaml.safe_load(open(yaml_path, "r"))
        except Exception:
            # TODO: Improve this message
            raise BuildUserError(
                "The required 'readthedocs-build.yaml' file was not provided."
            )

        log.info("readthedocs-build.yaml loaded.", path=yaml_path)

        # TODO: validate the YAML generated by the user
        # self._validate_readthedocs_data_yaml(data)

        # Populate the data provided by the doctool with data we have from the build context
        # TODO: this is the new structure that has to be defined
        # context = {
        #     "project": {
        #         "slug": self.data.project.slug,
        #     },
        #     "version": {
        #         "slug": self.data.version.slug,
        #     },
        #     "build": {
        #         "id": self.data.build["pk"],
        #     },
        # }

        # NOTE: this is the OLD structure.
        # This will be changed for a new structure that we have to decide yet.
        # I'm using the old one for now just to keep compatibility.
        context = {
            "ad_free": False,
            "api_host": "http://devthedocs.org",
            "build_date": timezone.now(),
            "builder": "$DOCTOOL_NAME",
            "canonical_url": self.data.project.canonical_url,
            "commit": self.data.build["commit"],
            "docroot": "$DOCTOOL_DOCROOT",
            "language": self.data.project.language,
            "page": "$DOCTOOL_PAGE",  # Can we define this dynamically via Javascript?
            "programming_language": self.data.project.programming_language,
            "project": self.data.project.slug,
            "version": self.data.version.slug,
            "source_suffix": "$DOCTOOL_SOURCE_SUFFIX",
            "theme": "$DOCTOOL_THEME",
            # These can be removed
            "user_analytics_code": None,
            "global_analytics_code": None,
            "proxied_api_host": f"/{settings.DOC_PATH_PREFIX}",
            "subprojects": None,
            # TODO: remove the following ones, they are just my own tests
            # NOTE: eventually, some of these settings should be enabled/disabled by the reader
            "build": {
                "id": self.data.build_pk,
                "external_version": self.data.version.type == EXTERNAL,
            },
            "repository_url": self.data.project.repo,
        }

        # Update user's generated data with our own data.
        data.update(context)

        js_path = os.path.join(
            self.data.project.artifact_path(
                version=self.data.version.slug, type_="html"
            ),
            "readthedocs-data.html",
        )
        content = render_to_string(
            template_name="doc_builder/readthedocs-data.html",
            context=dict(data=context),
        )
        with open(js_path, "w") as f:
            f.write(content)
        log.info("readthedocs-data.html written.", path=js_path)
