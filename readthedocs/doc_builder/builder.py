from django.conf import settings

# NOTE:
#
# 1. should we use the same structure for commands the user cannot override?
# For example, `git submodules` and `system_dependencies`.
#
# Re-using this structure makes it easier to follow the process of all the
# commands executed for build.
#
# 2. intenal Read the Docs actions (e.g update `Build`'s status) should not be
# part of this structure of pre/post actions. Those should be encapsulated at
# the Celery task level.


class DocumentationBuilder:
    def __init__(
        self,
        vcs_environment,
        vcs_repository,
        data,  # Celery task's ``data`` object
        language_environment=None,
    ):
        self.vcs_environment = vcs_environment
        self.vcs_repository = vcs_repository
        self.data = data
        self.vcs_repository = vcs_repository

    # VCS checkout
    def pre_checkout(self):
        raise NotImplementedError

    def checkout(self):
        self.vcs_repository.update()
        # TODO: checkout submodules here

    def post_checkout(self):
        command = self.config.build.jobs.post_checkout
        if command:
            self.run(command)

    # System dependencies (``build.apt_packages``)
    #
    # NOTE: system dependencies should not be possible to override by the user
    # because it's executed as ``root`` user.
    def pre_system_dependencies(self):
        """
        Update APT source lists.

        .. note::

           ``--quiet`` won't suppress the output,
           it would just remove the progress bar.
        """
        command = self.config.build.jobs.pre_system_dependencies
        if command:
            self.run(command)
        else:
            packages = self.data.config.build.apt_packages
            if packages:
                self.run(
                    "apt-get",
                    "update",
                    "--assume-yes",
                    "--quiet",
                    user=settings.RTD_DOCKER_SUPER_USER,
                )

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
            # put ``--`` to end all command arguments.
            self.run(
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
        command = self.config.build.jobs.pre_create_environment
        if command:
            self.run(command)

    def create_environment(self):
        command = self.config.build.jobs.create_environment
        if command:
            self.run(command)
        else:
            self.language_environment.setup_base()

    def post_create_environment(self):
        command = self.config.build.jobs.post_create_environment
        if command:
            self.run(command)

    # Install
    def pre_install(self):
        commands = self.config.build.jobs.pre_install
        for command in commands:
            self.run(command)

    def install(self):
        commands = self.config.build.jobs.install
        for command in commands:
            self.run(command)

        if not commands:
            self.language_environment.install_core_requirements()
            self.language_environment.install_requirements()

    def post_install(self):
        commands = self.config.build.jobs.post_install
        for command in commands:
            self.run(command)

    # Build
    def pre_build(self):
        commands = self.config.build.jobs.pre_build
        for command in commands:
            self.run(command)

    def build_html(self):
        commands = self.config.build.jobs.build.html
        for command in commands:
            self.run(command)
            # FIXME: always return `True` when the user provides the commands?
            return True

        if not commands:
            html_builder = get_builder_class(self.data.config.doctype)(
                build_env=self.data.build_env,
                python_env=self.data.python_env,
            )
            html_builder.append_conf()
            success = html_builder.build()
            if success:
                html_builder.move()

            return success

    def build_pdf(self):
        commands = self.config.build.jobs.build.pdf
        for command in commands:
            self.run(command)

        if not commands:
            # TODO: move this check logic back to the Celery task. We want to
            # run the command here only and do not return anything.
            if (
                "pdf" not in self.data.config.formats
                or self.data.version.type == EXTERNAL
            ):
                return False
            # Mkdocs has no pdf generation currently.
            if self.is_type_sphinx():
                return self.build_docs_class("sphinx_pdf")
            return False

    def build_htmlzip(self):
        commands = self.config.build.jobs.build.htmlzip
        for command in commands:
            self.run(command)
            # FIXME: always return `True` when the user provides the commands?
            return True

        if not commands:
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
        commands = self.config.build.jobs.build.epub
        for command in commands:
            self.run(command)
            # FIXME: always return `True` when the user provides the commands?
            return True

        if not commands:
            if (
                "epub" not in self.data.config.formats
                or self.data.version.type == EXTERNAL
            ):
                return False
            # Mkdocs has no epub generation currently.
            if self.is_type_sphinx():
                return self.build_docs_class("sphinx_epub")
            return False

    def post_build(self):
        commands = self.config.build.jobs.post_build
        for command in commands:
            self.run(command)

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
            self.data.build_env,
            python_env=self.data.python_env,
        )
        success = builder.build()
        builder.move()
        return success
