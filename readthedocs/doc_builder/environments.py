"""Documentation Builder Environments."""

import os
import re
import subprocess
import sys
import uuid
from datetime import datetime

import structlog
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from docker import APIClient
from docker.errors import APIError as DockerAPIError
from docker.errors import DockerException
from docker.errors import NotFound as DockerNotFoundError
from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout
from slumber.exceptions import HttpNotFoundError

from readthedocs.builds.models import BuildCommandResultMixin
from readthedocs.core.utils import slugify
from readthedocs.projects.models import Feature

from .constants import DOCKER_HOSTNAME_MAX_LEN
from .constants import DOCKER_IMAGE
from .constants import DOCKER_OOM_EXIT_CODE
from .constants import DOCKER_SOCKET
from .constants import DOCKER_TIMEOUT_EXIT_CODE
from .constants import DOCKER_VERSION
from .constants import RTD_SKIP_BUILD_EXIT_CODE
from .exceptions import BuildAppError
from .exceptions import BuildCancelled
from .exceptions import BuildUserError


log = structlog.get_logger(__name__)


def _truncate_output(output):
    if output is None:
        return ""
    output_lines = output.split("\n")
    if len(output_lines) <= 20:
        return output
    return "\n".join(output_lines[:10] + [" ..Output Truncated.. "] + output_lines[-10:])


class BuildCommand(BuildCommandResultMixin):
    """
    Wrap command execution for execution in build environments.

    This wraps subprocess commands with some logic to handle exceptions,
    logging, and setting up the env for the build command.

    This acts a mapping of sorts to the API representation of the
    :py:class:`readthedocs.builds.models.BuildCommandResult` model.

    :param command: string or array of command parameters
    :param cwd: Absolute path used as the current working path for the command.
        Defaults to ``RTD_DOCKER_WORKDIR``.
    :param shell: execute command in shell, default=False
    :param environment: environment variables to add to environment
    :type environment: dict
    :param str user: User used to execute the command, it can be in form of ``user:group``
        or ``user``. Defaults to ``RTD_DOCKER_USER``.
    :param build_env: build environment to use to execute commands
    :param bin_path: binary path to add to PATH resolution
    :param demux: Return stdout and stderr separately.
    :param kwargs: allow to subclass this class and extend it
    """

    def __init__(
        self,
        command,
        cwd=None,
        shell=False,
        environment=None,
        user=None,
        build_env=None,
        bin_path=None,
        record_as_success=False,
        demux=False,
        **kwargs,
    ):
        self.id = None
        self.command = command
        self.shell = shell
        self.cwd = cwd or settings.RTD_DOCKER_WORKDIR
        self.user = user or settings.RTD_DOCKER_USER
        self._environment = environment.copy() if environment else {}
        if "PATH" in self._environment:
            raise BuildAppError(
                BuildAppError.GENERIC_WITH_BUILD_ID,
                exception_message="'PATH' can't be set. Use bin_path",
            )

        self.build_env = build_env
        self.output = None
        self.error = None
        self.start_time = None
        self.end_time = None

        self.bin_path = bin_path
        self.record_as_success = record_as_success
        self.demux = demux
        self.exit_code = None

        # NOTE: `self.build_env` is not available when instantiating this class
        # from hacky tests. `Project.vcs_repo` allows not passing an
        # environment, which makes all the commands to fail, because there is
        # no environment to run them.
        #
        # Maybe this ``BuildCommand`` should not accept `build_env=None` since
        # it doesn't make sense.
        if self.build_env:
            # When using `project.vcs_repo` on tests we are passing `environment=False`.
            # See https://github.com/readthedocs/readthedocs.org/pull/6482#discussion_r367694530
            if self.build_env.project and self.build_env.version:
                structlog.contextvars.bind_contextvars(
                    project_slug=self.build_env.project.slug,
                    version_slug=self.build_env.version.slug,
                )

            # NOTE: `self.build_env.build` is not available when using this class
            # from `sync_repository_task` since it's not associated to any build
            if self.build_env.build:
                structlog.contextvars.bind_contextvars(
                    build_id=self.build_env.build.get("id"),
                )

    def __str__(self):
        # TODO do we want to expose the full command here?
        output = ""
        if self.output is not None:
            output = self.output.encode("utf-8")
        return "\n".join([self.get_command(), output])

    # TODO: remove this `run` method. We are using it on tests, so we need to
    # find a way to change this. NOTE: it uses `subprocess.Popen` to run
    # commands, which is not supported anymore
    def run(self):
        """Set up subprocess and execute command."""
        self.start_time = datetime.utcnow()
        environment = self._environment.copy()
        if "DJANGO_SETTINGS_MODULE" in environment:
            del environment["DJANGO_SETTINGS_MODULE"]
        if "PYTHONPATH" in environment:
            del environment["PYTHONPATH"]

        # Always copy the PATH from the host into the environment
        env_paths = os.environ.get("PATH", "").split(":")
        if self.bin_path is not None:
            env_paths.insert(0, self.bin_path)
        environment["PATH"] = ":".join(env_paths)

        log.info(
            "Running build command.",
            command=self.get_command(),
            cwd=self.cwd,
            environment=environment,
        )

        try:
            # When using ``shell=True`` the command should be flatten
            command = self.command
            if self.shell:
                command = self.get_command()

            stderr = subprocess.PIPE if self.demux else subprocess.STDOUT
            proc = subprocess.Popen(  # pylint: disable=consider-using-with
                command,
                shell=self.shell,
                cwd=self.cwd,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=stderr,
                env=environment,
            )
            cmd_stdout, cmd_stderr = proc.communicate()
            self.output = self.decode_output(cmd_stdout)
            self.error = self.decode_output(cmd_stderr)
            self.exit_code = proc.returncode
        except OSError:
            log.exception("Operating system error.")
            self.exit_code = -1
        finally:
            self.end_time = datetime.utcnow()

    def decode_output(self, output: bytes) -> str:
        """Decode bytes output to a UTF-8 string."""
        decoded = ""
        try:
            decoded = output.decode("utf-8", "replace")
        except (TypeError, AttributeError):
            pass
        return decoded

    def sanitize_output(self, output: str) -> str:
        r"""
        Sanitize ``output`` to be saved into the DB.

            1. Replaces NULL (\x00) characters with ``''`` (empty string) to
               avoid PostgreSQL db to fail:
               https://code.djangoproject.com/ticket/28201

            2. Chunk at around ``DATA_UPLOAD_MAX_MEMORY_SIZE`` bytes to be sent
               over the API call request

            3. Obfuscate private environment variables.

        :param output: stdout/stderr to be sanitized

        :returns: sanitized output as string
        """
        sanitized = ""
        try:
            # Replace NULL (\x00) character to avoid PostgreSQL db to fail
            # https://code.djangoproject.com/ticket/28201
            sanitized = output.replace("\x00", "")
        except (TypeError, AttributeError):
            pass

        # Chunk the output data to be less than ``DATA_UPLOAD_MAX_MEMORY_SIZE``
        # The length is calculated in bytes, so we need to encode the string first.
        # TODO: we are calculating the length in bytes, but truncating the string
        # in characters. We should use bytes or characters, but not both.
        output_length = len(sanitized.encode("utf-8"))
        # Left some extra space for the rest of the request data
        threshold = 512 * 1024  # 512Kb
        allowed_length = settings.DATA_UPLOAD_MAX_MEMORY_SIZE - threshold
        if output_length > allowed_length:
            log.info(
                "Command output is too big.",
                command=self.get_command(),
            )
            truncated_output = sanitized[-allowed_length:]
            sanitized = (
                ".. (truncated) ...\n"
                f"Output is too big. Truncated at {allowed_length} bytes.\n\n\n"
                f"{truncated_output}"
            )

        # Obfuscate private environment variables.
        if self.build_env:
            # NOTE: we can't use `self._environment` here because we don't know
            # which variable is public/private since it's just a name/value
            # dictionary. We need to check with the APIProject object (`self.build_env.project`).
            for name, spec in self.build_env.project._environment_variables.items():
                if not spec["public"]:
                    value = spec["value"]
                    obfuscated_value = f"{value[:4]}****"
                    sanitized = sanitized.replace(value, obfuscated_value)

        return sanitized

    def get_command(self):
        """Flatten command."""
        if hasattr(self.command, "__iter__") and not isinstance(self.command, str):
            return " ".join(self.command)
        return self.command

    def save(self, api_client):
        """
        Save this command and result via the API.

        The command can be saved before or after it has been run,
        if it's saved before it has been run, the exit_code,
        start_time, and end_time will be None.

        If the command is saved twice (before and after it has been run),
        the second save will update the command instead of creating a new one.
        The id of the command will be set the first time it is saved,
        so it can be used to update the command later.
        """
        # Force record this command as success to avoid Build reporting errors
        # on commands that are just for checking purposes and do not interferes
        # in the Build
        if self.record_as_success and self.exit_code is not None:
            log.warning("Recording command exit_code as success")
            self.exit_code = 0

        data = {
            "build": self.build_env.build.get("id"),
            "command": self.get_command(),
            "output": self.sanitize_output(self.output),
            "exit_code": self.exit_code,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

        # If the command has an id, it means it has been saved before,
        # so we update it instead of creating a new one.
        if self.id:
            try:
                resp = api_client.command(self.id).patch(data)
            except HttpNotFoundError:
                # TODO don't do this, address builds restarting instead.
                # We try to post the buildcommand again as a temporary fix
                # for projects that restart the build process. There seems to be
                # something that causes a 404 during `patch()` in some biulds,
                # so we assume retrying `post()` for the build command is okay.
                log.exception("Build command has an id but doesn't exist in the database.")
                resp = api_client.command.post(data)
        else:
            resp = api_client.command.post(data)

        log.debug("Response via JSON encoded data.", response=resp)

        self.id = resp.get("id")


class DockerBuildCommand(BuildCommand):
    """
    Create a docker container and run a command inside the container.

    Build command to execute in docker container
    """

    bash_escape_re = re.compile(
        r"([\s\!\"\#\$\&\'\(\)\*\:\;\<\>\?\@\[\\\]\^\`\{\|\}\~])"  # noqa
    )

    def __init__(self, *args, escape_command=True, **kwargs):
        """
        Override default to extend behavior.

        :param escape_command: whether escape special chars the command before
            executing it in the container. This should only be disabled on
            trusted or internal commands.
        :type escape_command: bool
        """
        self.escape_command = escape_command
        super().__init__(*args, **kwargs)

    def run(self):
        """Execute command in existing Docker container."""
        log.info(
            "Running build command in container.",
            container_id=self.build_env.container_id,
            command=self.get_command(),
            cwd=self.cwd,
        )

        self.start_time = datetime.utcnow()
        client = self.build_env.get_client()
        try:
            exec_cmd = client.exec_create(
                container=self.build_env.container_id,
                cmd=self.get_wrapped_command(),
                environment=self._environment,
                user=self.user,
                workdir=self.cwd,
                stdout=True,
                stderr=True,
            )

            out = client.exec_start(exec_id=exec_cmd["Id"], stream=False, demux=self.demux)
            cmd_stdout = ""
            cmd_stderr = ""
            if self.demux:
                cmd_stdout, cmd_stderr = out
            else:
                cmd_stdout = out
            self.output = self.decode_output(cmd_stdout)
            self.error = self.decode_output(cmd_stderr)
            cmd_ret = client.exec_inspect(exec_id=exec_cmd["Id"])
            self.exit_code = cmd_ret["ExitCode"]

            # Docker will exit with a special exit code to signify the command
            # was killed due to memory usage. We try to make the error code
            # nicer here. However, sometimes the kernel kills the command and
            # Docker does not use the specific exit code, so we check if the
            # word `Killed` is in the last 15 lines of the command's output.
            #
            # NOTE: the work `Killed` could appear in the output because the
            # command was killed by OOM or timeout so we put a generic message here.
            killed_in_output = "Killed" in "\n".join(
                self.output.splitlines()[-15:],
            )
            if self.exit_code == DOCKER_OOM_EXIT_CODE or (self.exit_code == 1 and killed_in_output):
                self.output += str(
                    _(
                        "\n\nCommand killed due to timeout or excessive memory consumption\n",
                    ),
                )
        except DockerAPIError:
            self.exit_code = -1
            if self.output is None or not self.output:
                self.output = _("Command exited abnormally")
        finally:
            self.end_time = datetime.utcnow()

    def get_wrapped_command(self):
        """
        Wrap command in a shell and optionally escape special bash characters.

        In order to set the current working path inside a docker container, we
        need to wrap the command in a shell call manually.

        Some characters will be interpreted as shell characters without
        escaping, such as: ``pip install requests<0.8``. When passing
        ``escape_command=True`` in the init method this escapes a good majority
        of those characters.
        """
        prefix = ""
        if self.bin_path:
            bin_path = self._escape_command(self.bin_path)
            prefix += f"PATH={bin_path}:$PATH "

        command = " ".join(
            self._escape_command(part) if self.escape_command else part for part in self.command
        )
        if prefix:
            # Using `;` or `\n` to separate the `prefix` where we define the
            # variables with the `command` itself, have the same effect.
            # However, using `;` is more explicit.
            # See https://github.com/readthedocs/readthedocs.org/pull/10334
            return f"/bin/sh -c '{prefix}; {command}'"
        return f"/bin/sh -c '{command}'"

    def _escape_command(self, cmd):
        r"""Escape the command by prefixing suspicious chars with `\`."""
        command = self.bash_escape_re.sub(r"\\\1", cmd)

        # HACK: avoid escaping variables that we need to use in the commands
        not_escape_variables = (
            "READTHEDOCS_OUTPUT",
            "READTHEDOCS_VIRTUALENV_PATH",
            "READTHEDOCS_GIT_CLONE_TOKEN",
            "CONDA_ENVS_PATH",
            "CONDA_DEFAULT_ENV",
        )
        for variable in not_escape_variables:
            command = command.replace(f"\\${variable}", f"${variable}")
        return command


class BaseBuildEnvironment:
    """
    Base build environment.

    Base class for wrapping command execution for build steps. This class is in
    charge of raising ``BuildAppError`` for internal application errors that
    should be communicated to the user as a general unknown error and
    ``BuildUserError`` that will be exposed to the user with a proper message
    for them to debug by themselves since they are _not_ a Read the Docs issue.

    :param project: Project that is being built
    :param version: Project version that is being built
    :param build: Build instance
    :param environment: shell environment variables
    :param record: whether or not record a build commands in the databse via
     the API. The only case where we want this to be `False` is when
     instantiating this class from `sync_repository_task` because it's a
     background task that does not expose commands to the user.
    :param api_client: API v2 client instance (readthedocs.v2.client).
     This is used to record commands in the database, if `record=True`
     this argument is required.
    """

    def __init__(
        self,
        project=None,
        version=None,
        build=None,
        config=None,
        environment=None,
        record=True,
        api_client=None,
        **kwargs,
    ):
        self.project = project
        self._environment = environment or {}
        self.commands = []
        self.version = version
        self.build = build
        self.config = config
        self.record = record
        self.api_client = api_client

        if self.record and not self.api_client:
            raise ValueError("api_client is required when record=True")

    # TODO: remove these methods, we are not using LocalEnvironment anymore. We
    # need to find a way for tests to not require this anymore
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return

    def record_command(self, command):
        if self.record:
            command.save(self.api_client)

    def run(self, *cmd, **kwargs):
        """Shortcut to run command from environment."""
        return self.run_command_class(cls=self.command_class, cmd=cmd, **kwargs)

    def run_command_class(
        self, cls, cmd, warn_only=False, record=True, record_as_success=False, **kwargs
    ):
        """
        Run command from this environment.

        :param cls: command class to instantiate a command
        :param cmd: command (as a list) to execute in this environment
        :param record: whether or not to record this particular command
            (``False`` implies ``warn_only=True``)
        :param warn_only: don't raise an exception on command failure
        :param record_as_success: force command ``exit_code`` to be saved as
            ``0`` (``True`` implies ``warn_only=True`` and ``record=True``)
        """
        if not record:
            warn_only = True

        if record_as_success:
            record = True
            warn_only = True
            # ``record_as_success`` is needed to instantiate the BuildCommand
            kwargs.update({"record_as_success": record_as_success})

        # Remove PATH from env, and set it to bin_path if it isn't passed in
        environment = self._environment.copy()
        env_path = environment.pop("BIN_PATH", None)
        if "bin_path" not in kwargs and env_path:
            kwargs["bin_path"] = env_path
        if "environment" in kwargs:
            raise BuildAppError(
                BuildAppError.GENERIC_WITH_BUILD_ID,
                exception_message="environment can't be passed in via commands.",
            )
        kwargs["environment"] = environment
        kwargs["build_env"] = self
        build_cmd = cls(cmd, **kwargs)

        # Save the command that's running before it starts,
        # then we will update the results after it has run.
        if record:
            self.record_command(build_cmd)
            # We want append this command to the list of commands only if it has
            # to be recorded in the database (to keep consistency) and also, it
            # has to be added after ``self.record_command`` since its
            # ``exit_code`` can be altered because of ``record_as_success``
            self.commands.append(build_cmd)

        build_cmd.run()

        if record:
            # TODO: I don't like how it's handled this entry point here since
            # this class should know nothing about a BuildCommand (which are the
            # only ones that can be saved/recorded)
            self.record_command(build_cmd)

        if build_cmd.failed:
            if warn_only:
                msg = "Command failed"
                log.warning(
                    msg,
                    command=build_cmd.get_command(),
                    output=_truncate_output(build_cmd.output),
                    stderr=_truncate_output(build_cmd.error),
                    exit_code=build_cmd.exit_code,
                    project_slug=self.project.slug if self.project else "",
                    version_slug=self.version.slug if self.version else "",
                )
            elif build_cmd.exit_code == RTD_SKIP_BUILD_EXIT_CODE:
                raise BuildCancelled(BuildCancelled.SKIPPED_EXIT_CODE_183)
            else:
                # TODO: for now, this still outputs a generic error message
                # that is the same across all commands. We could improve this
                # with more granular error messages that vary by the command
                # being run.
                raise BuildUserError(BuildUserError.GENERIC)
        return build_cmd


class LocalBuildEnvironment(BaseBuildEnvironment):
    """Local execution build environment."""

    command_class = BuildCommand


class DockerBuildEnvironment(BaseBuildEnvironment):
    """
    Docker build environment, uses docker to contain builds.

    If :py:data:`settings.DOCKER_ENABLE` is true, build documentation inside a
    docker container, instead of the host system, using this build environment
    class.  The build command creates a docker container from a pre-built image,
    defined by :py:data:`settings.DOCKER_IMAGE`.  This container is started with
    a mount to the project's build path under ``user_builds`` on the host
    machine, walling off project builds from reading/writing other projects'
    data.
    """

    command_class = DockerBuildCommand
    container_image = DOCKER_IMAGE

    @staticmethod
    def _get_docker_exception_message(exc):
        """Return a human readable message from a Docker exception."""

        # ``docker.errors.DockerException`` usually exposes ``explanation`` but
        # some subclasses created when wrapping other libraries (``requests``,
        # ``urllib3``) do not. Accessing it blindly raises ``AttributeError``.
        # Fallback to ``str(exc)`` so we always have a useful message.
        message = getattr(exc, "explanation", None)
        if not message:
            message = str(exc)
        if not message:
            message = repr(exc)
        return message

    def __init__(self, *args, **kwargs):
        container_image = kwargs.pop("container_image", None)
        super().__init__(*args, **kwargs)
        self.client = None
        self.container = None
        self.container_name = self.get_container_name()

        # Decide what Docker image to use, based on priorities:
        # The image set by user or,
        if self.config and self.config.docker_image:
            self.container_image = self.config.docker_image
        # the image overridden by the project (manually set by an admin).
        if self.project.container_image:
            self.container_image = self.project.container_image

        # Override the ``container_image`` if we pass it via argument.
        #
        # FIXME: This is a temporal fix while we explore how to make
        # ``ubuntu-20.04`` the default build image without breaking lot of
        # builds. For now, we are passing
        # ``container_image='readthedocs/build:ubuntu-20.04'`` for the setup
        # VCS step.
        if container_image:
            self.container_image = container_image

        self.container_mem_limit = self.project.container_mem_limit or settings.BUILD_MEMORY_LIMIT
        self.container_time_limit = self.project.container_time_limit or settings.BUILD_TIME_LIMIT

        structlog.contextvars.bind_contextvars(
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )

        # NOTE: as this environment is used for `sync_repository_task` it may
        # not have a build associated
        if self.build:
            structlog.contextvars.bind_contextvars(
                build_id=self.build.get("id"),
            )

    def __enter__(self):
        """Start of environment context."""
        try:
            # Test for existing container. We remove any stale containers that
            # are no longer running here if there is a collision. We throw an
            # exception
            state = self.container_state()
            if state is not None:
                if state.get("Running") is True:
                    raise BuildAppError(
                        BuildAppError.GENERIC_WITH_BUILD_ID,
                        exception_message=_(
                            "A build environment is currently running for this version",
                        ),
                    )

                log.warning(
                    "Removing stale container.",
                    container_id=self.container_id,
                )
                client = self.get_client()
                client.remove_container(self.container_id)
        except (DockerAPIError, ConnectionError) as exc:
            raise BuildAppError(
                BuildAppError.GENERIC_WITH_BUILD_ID,
                exception_message=self._get_docker_exception_message(exc),
            ) from exc

        # Create the checkout path if it doesn't exist to avoid Docker creation
        if not os.path.exists(self.project.doc_path):
            os.makedirs(self.project.doc_path)

        try:
            self.create_container()
        except:  # noqa
            self.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """End of environment context."""
        client = self.get_client()
        try:
            client.kill(self.container_id)
        except DockerNotFoundError:
            log.info(
                "Container does not exists, nothing to kill.",
                container_id=self.container_id,
            )
        except DockerAPIError:
            # Logging this as warning because it usually happens due memory
            # limit or build timeout. In those cases, the container is not
            # running and can't be killed
            log.warning(
                "Unable to kill container.",
                container_id=self.container_id,
            )

        # Save the container's state before removing it to know what exception
        # to raise in the next step (`update_build_from_container_state`)
        state = self.container_state()

        try:
            log.info("Removing container.", container_id=self.container_id)
            client.remove_container(self.container_id)
        except DockerNotFoundError:
            log.info(
                "Container does not exists, nothing to remove.",
                container_id=self.container_id,
            )
        # Catch direct failures from Docker API or with an HTTP request.
        # These errors should not surface to the user.
        except (DockerAPIError, ConnectionError, ReadTimeout):
            log.exception("Couldn't remove container")

        self.raise_container_error(state)

    def get_container_name(self):
        if self.build:
            name = "build-{build}-project-{project_id}-{project_name}".format(
                build=self.build.get("id"),
                project_id=self.project.pk,
                project_name=self.project.slug,
            )
        else:
            # An uuid is added, so the container name is unique per sync.
            uuid_ = uuid.uuid4().hex[:8]
            name = f"sync-{uuid_}-project-{self.project.pk}-{self.project.slug}"
        return slugify(name[:DOCKER_HOSTNAME_MAX_LEN])

    def get_client(self):
        """Create Docker client connection."""
        try:
            if self.client is None:
                self.client = APIClient(
                    base_url=DOCKER_SOCKET,
                    version=DOCKER_VERSION,
                )
            return self.client
        except DockerException as exc:
            raise BuildAppError(
                BuildAppError.GENERIC_WITH_BUILD_ID,
                exception_message=self._get_docker_exception_message(exc),
            ) from exc

    def _get_binds(self):
        """
        Return proper Docker Binds depending on settings.

        It uses Docker Volume if running on a docker-compose. Otherwise, it
        returns just a regular mountpoint path.
        """
        if getattr(settings, "RTD_DOCKER_COMPOSE", False):
            from pathlib import Path

            binds = {
                settings.RTD_DOCKER_COMPOSE_VOLUME: {
                    "bind": str(Path(settings.DOCROOT).parent),
                    "mode": "rw",
                },
            }
        else:
            binds = {
                self.project.doc_path: {
                    "bind": self.project.doc_path,
                    "mode": "rw",
                },
            }

        binds.update(settings.RTD_DOCKER_ADDITIONAL_BINDS)

        return binds

    def get_container_host_config(self):
        """
        Create the ``host_config`` settings for the container.

        It mainly generates the proper path bindings between the Docker
        container and the Host by mounting them with the proper permissions.

        The object returned is passed to Docker function
        ``client.create_container``.
        """
        return self.get_client().create_host_config(
            binds=self._get_binds(),
            mem_limit=self.container_mem_limit,
        )

    @property
    def container_id(self):
        """Return id of container if it is valid."""
        if self.container_name:
            return self.container_name

        if self.container:
            return self.container.get("Id")

    def container_state(self):
        """Get container state."""
        client = self.get_client()
        try:
            info = client.inspect_container(self.container_id)
            return info.get("State", {})
        except DockerAPIError:
            return None

    def raise_container_error(self, state):
        """
        Raise an exception based on the container's state.

        In the case of the parent command exiting before the exec commands
        finish, or in the case of OOM on the container, raise a
        `BuildUserError` with an error message explaining the failure.
        Otherwise, raise a `BuildAppError`.
        """
        if state is not None and state.get("Running") is False:
            if state.get("ExitCode") == DOCKER_TIMEOUT_EXIT_CODE:
                raise BuildUserError(message_id=BuildUserError.BUILD_TIME_OUT)

            if state.get("OOMKilled", False):
                raise BuildUserError(message_id=BuildUserError.BUILD_EXCESSIVE_MEMORY)

            if state.get("Error"):
                raise BuildAppError(
                    message_id=BuildAppError.BUILD_DOCKER_UNKNOWN_ERROR,
                    format_values={
                        "message": state.get("Error"),
                    },
                )

    def create_container(self):
        """Create docker container."""
        client = self.get_client()
        try:
            log.info(
                "Creating Docker container.",
                container_image=self.container_image,
                container_id=self.container_id,
                container_time_limit=self.container_time_limit,
                container_mem_limit=self.container_mem_limit,
            )

            networking_config = None
            if settings.RTD_DOCKER_COMPOSE:
                # Create the container in the same network the web container is
                # running, so we can hit its healthcheck API.
                networking_config = client.create_networking_config(
                    {
                        settings.RTD_DOCKER_COMPOSE_NETWORK: client.create_endpoint_config(),
                    }
                )

            self.container = client.create_container(
                image=self.container_image,
                command=(
                    '/bin/sh -c "sleep {time}; exit {exit}"'.format(
                        time=self.container_time_limit,
                        exit=DOCKER_TIMEOUT_EXIT_CODE,
                    )
                ),
                name=self.container_id,
                hostname=self.container_id,
                host_config=self.get_container_host_config(),
                detach=True,
                user=settings.RTD_DOCKER_USER,
                runtime="runsc",  # gVisor runtime
                networking_config=networking_config,
            )
            client.start(container=self.container_id)

            # NOTE: as this environment is used for `sync_repository_task` it may
            # not have a build associated. We skip running a healthcheck on those cases.
            if self.project.has_feature(Feature.BUILD_HEALTHCHECK) and self.build:
                self._run_background_healthcheck()

        except (DockerAPIError, ConnectionError) as exc:
            raise BuildAppError(
                BuildAppError.GENERIC_WITH_BUILD_ID,
                exception_message=self._get_docker_exception_message(exc),
            ) from exc

    def _run_background_healthcheck(self):
        """
        Run a cURL command in the background to ping the healthcheck API.

        The API saves the last ping timestamp on each call. Then a periodic Celery task
        checks this value for all the running builds and decide if the build is stalled or not.
        If it's stalled, it terminates those builds and mark them as fail.
        """
        log.debug("Running build with healthcheck.")

        build_id = self.build.get("id")
        build_builder = self.build.get("builder")
        healthcheck_url = reverse("build-healthcheck", kwargs={"pk": build_id})
        url = f"{settings.SLUMBER_API_HOST}{healthcheck_url}?builder={build_builder}"

        # We use --insecure because we are hitting the internal load balancer here that doesn't have a SSL certificate
        # The -H "Host: " header is required because of internal load balancer URL
        cmd = f"/bin/bash -c 'while true; do curl --insecure --max-time 2 -H \"Host: {settings.PRODUCTION_DOMAIN}\" -X POST {url}; sleep {settings.RTD_BUILD_HEALTHCHECK_DELAY}; done;'"
        log.info("Healthcheck command to run.", command=cmd)

        client = self.get_client()
        exec_cmd = client.exec_create(
            container=self.container_id,
            cmd=cmd,
            user=settings.RTD_DOCKER_USER,
            stdout=True,
            stderr=True,
        )
        # `detach=True` allows us to run this command in the background
        client.exec_start(exec_id=exec_cmd["Id"], stream=False, detach=True)
