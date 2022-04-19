"""Documentation Builder Environments."""

import os
import re
import subprocess
import sys
import uuid
from datetime import datetime

import structlog
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from docker import APIClient
from docker.errors import APIError as DockerAPIError
from docker.errors import DockerException
from docker.errors import NotFound as DockerNotFoundError
from requests.exceptions import ConnectionError, ReadTimeout
from requests_toolbelt.multipart.encoder import MultipartEncoder

from readthedocs.api.v2.client import api as api_v2
from readthedocs.builds.models import BuildCommandResultMixin
from readthedocs.core.utils import slugify
from readthedocs.projects.models import Feature

from .constants import (
    DOCKER_HOSTNAME_MAX_LEN,
    DOCKER_IMAGE,
    DOCKER_LIMITS,
    DOCKER_OOM_EXIT_CODE,
    DOCKER_SOCKET,
    DOCKER_TIMEOUT_EXIT_CODE,
    DOCKER_VERSION,
)
from .exceptions import BuildAppError, BuildUserError

log = structlog.get_logger(__name__)


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
            **kwargs,
    ):
        self.command = command
        self.shell = shell
        self.cwd = cwd or settings.RTD_DOCKER_WORKDIR
        self.user = user or settings.RTD_DOCKER_USER
        self._environment = environment.copy() if environment else {}
        if 'PATH' in self._environment:
            raise BuildAppError('\'PATH\' can\'t be set. Use bin_path')

        self.build_env = build_env
        self.output = None
        self.error = None
        self.start_time = None
        self.end_time = None

        self.bin_path = bin_path
        self.record_as_success = record_as_success
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
                log.bind(
                    project_slug=self.build_env.project.slug,
                    version_slug=self.build_env.version.slug,
                )

            # NOTE: `self.build_env.build` is not available when using this class
            # from `sync_repository_task` since it's not associated to any build
            if self.build_env.build:
                log.bind(
                    build_id=self.build_env.build.get('id'),
                )

    def __str__(self):
        # TODO do we want to expose the full command here?
        output = ''
        if self.output is not None:
            output = self.output.encode('utf-8')
        return '\n'.join([self.get_command(), output])

    # TODO: remove this `run` method. We are using it on tests, so we need to
    # find a way to change this. NOTE: it uses `subprocess.Popen` to run
    # commands, which is not supported anymore
    def run(self):
        """Set up subprocess and execute command."""
        log.info("Running build command.", command=self.get_command(), cwd=self.cwd)

        self.start_time = datetime.utcnow()
        environment = self._environment.copy()
        if 'DJANGO_SETTINGS_MODULE' in environment:
            del environment['DJANGO_SETTINGS_MODULE']
        if 'PYTHONPATH' in environment:
            del environment['PYTHONPATH']

        # Always copy the PATH from the host into the environment
        env_paths = os.environ.get('PATH', '').split(':')
        if self.bin_path is not None:
            env_paths.insert(0, self.bin_path)
        environment['PATH'] = ':'.join(env_paths)

        try:
            # When using ``shell=True`` the command should be flatten
            command = self.command
            if self.shell:
                command = self.get_command()

            proc = subprocess.Popen(
                command,
                shell=self.shell,
                cwd=self.cwd,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=environment,
            )
            cmd_stdout, cmd_stderr = proc.communicate()
            self.output = self.sanitize_output(cmd_stdout)
            self.error = self.sanitize_output(cmd_stderr)
            self.exit_code = proc.returncode
        except OSError:
            log.exception("Operating system error.")
            self.exit_code = -1
        finally:
            self.end_time = datetime.utcnow()

    def sanitize_output(self, output):
        r"""
        Sanitize ``output`` to be saved into the DB.

            1. Decodes to UTF-8

            2. Replaces NULL (\x00) characters with ``''`` (empty string) to
               avoid PostgreSQL db to fail:
               https://code.djangoproject.com/ticket/28201

            3. Chunk at around ``DATA_UPLOAD_MAX_MEMORY_SIZE`` bytes to be sent
               over the API call request

        :param output: stdout/stderr to be sanitized
        :type output: bytes

        :returns: sanitized output as string or ``None`` if it fails
        """
        try:
            sanitized = output.decode('utf-8', 'replace')
            # Replace NULL (\x00) character to avoid PostgreSQL db to fail
            # https://code.djangoproject.com/ticket/28201
            sanitized = sanitized.replace('\x00', '')
        except (TypeError, AttributeError):
            sanitized = None

        # Chunk the output data to be less than ``DATA_UPLOAD_MAX_MEMORY_SIZE``
        output_length = len(output) if output else 0
        # Left some extra space for the rest of the request data
        threshold = 512 * 1024  # 512Kb
        allowed_length = settings.DATA_UPLOAD_MAX_MEMORY_SIZE - threshold
        if output_length > allowed_length:
            log.info(
                'Command output is too big.',
                command=self.get_command(),
            )
            truncated_output = sanitized[-allowed_length:]
            sanitized = (
                '.. (truncated) ...\n'
                f'Output is too big. Truncated at {allowed_length} bytes.\n\n\n'
                f'{truncated_output}'
            )

        return sanitized

    def get_command(self):
        """Flatten command."""
        if hasattr(self.command, '__iter__') and not isinstance(self.command, str):
            return ' '.join(self.command)
        return self.command

    def save(self):
        """Save this command and result via the API."""
        # Force record this command as success to avoid Build reporting errors
        # on commands that are just for checking purposes and do not interferes
        # in the Build
        if self.record_as_success:
            log.warning('Recording command exit_code as success')
            self.exit_code = 0

        data = {
            'build': self.build_env.build.get('id'),
            'command': self.get_command(),
            'output': self.output,
            'exit_code': self.exit_code,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }

        if self.build_env.project.has_feature(Feature.API_LARGE_DATA):
            # Don't use slumber directly here. Slumber tries to enforce a string,
            # which will break our multipart encoding here.
            encoder = MultipartEncoder(
                {key: str(value) for key, value in data.items()}
            )
            resource = api_v2.command
            resp = resource._store['session'].post(
                resource._store['base_url'] + '/',
                data=encoder,
                headers={
                    'Content-Type': encoder.content_type,
                }
            )
            log.debug('Post response via multipart form.', response=resp)
        else:
            resp = api_v2.command.post(data)
            log.debug('Post response via JSON encoded data.', response=resp)


class DockerBuildCommand(BuildCommand):

    """
    Create a docker container and run a command inside the container.

    Build command to execute in docker container
    """

    bash_escape_re = re.compile(
        r"([\t\ \!\"\#\$\&\'\(\)\*\:\;\<\>\?\@"
        r'\[\\\]\^\`\{\|\}\~])'
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

            cmd_output = client.exec_start(exec_id=exec_cmd['Id'], stream=False)
            self.output = self.sanitize_output(cmd_output)
            cmd_ret = client.exec_inspect(exec_id=exec_cmd['Id'])
            self.exit_code = cmd_ret['ExitCode']

            # Docker will exit with a special exit code to signify the command
            # was killed due to memory usage. We try to make the error code
            # nicer here. However, sometimes the kernel kills the command and
            # Docker does not use the specific exit code, so we check if the
            # word `Killed` is in the last 15 lines of the command's output.
            #
            # NOTE: the work `Killed` could appear in the output because the
            # command was killed by OOM or timeout so we put a generic message here.
            killed_in_output = 'Killed' in '\n'.join(
                self.output.splitlines()[-15:],
            )
            if self.exit_code == DOCKER_OOM_EXIT_CODE or (
                self.exit_code == 1 and
                killed_in_output
            ):
                self.output += str(
                    _(
                        '\n\nCommand killed due to timeout or excessive memory consumption\n',
                    ),
                )
        except DockerAPIError:
            self.exit_code = -1
            if self.output is None or not self.output:
                self.output = _('Command exited abnormally')
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
        prefix = ''
        if self.bin_path:
            bin_path = self._escape_command(self.bin_path)
            prefix += f'PATH={bin_path}:$PATH '

        command = (
            ' '.join(
                self._escape_command(part) if self.escape_command else part
                for part in self.command
            )
        )
        return (
            "/bin/sh -c '{prefix}{cmd}'".format(
                prefix=prefix,
                cmd=command,
            )
        )

    def _escape_command(self, cmd):
        r"""Escape the command by prefixing suspicious chars with `\`."""
        return self.bash_escape_re.sub(r'\\\1', cmd)


class BaseEnvironment:

    """
    Base environment class.

    Used to run arbitrary commands outside a build.
    """

    def __init__(self, project, environment=None):
        # TODO: maybe we can remove this Project dependency also
        self.project = project
        self._environment = environment or {}
        self.commands = []

    def record_command(self, command):
        pass

    def run(self, *cmd, **kwargs):
        """Shortcut to run command from environment."""
        return self.run_command_class(cls=self.command_class, cmd=cmd, **kwargs)

    def run_command_class(
            self, cls, cmd, warn_only=False,
            record=True, record_as_success=False, **kwargs
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
            kwargs.update({'record_as_success': record_as_success})

        # Remove PATH from env, and set it to bin_path if it isn't passed in
        environment = self._environment.copy()
        env_path = environment.pop('BIN_PATH', None)
        if 'bin_path' not in kwargs and env_path:
            kwargs['bin_path'] = env_path
        if 'environment' in kwargs:
            raise BuildAppError('environment can\'t be passed in via commands.')
        kwargs['environment'] = environment

        # ``build_env`` is passed as ``kwargs`` when it's called from a
        # ``*BuildEnvironment``
        build_cmd = cls(cmd, **kwargs)
        build_cmd.run()

        if record:
            # TODO: I don't like how it's handled this entry point here since
            # this class should know nothing about a BuildCommand (which are the
            # only ones that can be saved/recorded)
            self.record_command(build_cmd)

            # We want append this command to the list of commands only if it has
            # to be recorded in the database (to keep consistency) and also, it
            # has to be added after ``self.record_command`` since its
            # ``exit_code`` can be altered because of ``record_as_success``
            self.commands.append(build_cmd)

        if build_cmd.failed:
            if warn_only:
                msg = 'Command {cmd} failed'.format(cmd=build_cmd.get_command())
                if build_cmd.output:
                    msg += ':\n{out}'.format(out=build_cmd.output)
                log.warning(
                    msg,
                    project_slug=self.project.slug if self.project else '',
                    version_slug=self.version.slug if self.version else '',
                )
            else:
                # TODO: for now, this still outputs a generic error message
                # that is the same across all commands. We could improve this
                # with more granular error messages that vary by the command
                # being run.
                raise BuildUserError()
        return build_cmd


class LocalEnvironment(BaseEnvironment):

    # TODO: BuildCommand name doesn't make sense here, should be just Command
    command_class = BuildCommand


class BuildEnvironment(BaseEnvironment):

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
    """

    def __init__(
            self,
            project=None,
            version=None,
            build=None,
            config=None,
            environment=None,
            record=True,
            **kwargs,
    ):
        super().__init__(project, environment)
        self.version = version
        self.build = build
        self.config = config
        self.record = record

    # TODO: remove these methods, we are not using LocalEnvironment anymore. We
    # need to find a way for tests to not require this anymore
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return

    def record_command(self, command):
        if self.record:
            command.save()

    def run(self, *cmd, **kwargs):
        kwargs.update({
            'build_env': self,
        })
        return super().run(*cmd, **kwargs)

    def run_command_class(self, *cmd, **kwargs):  # pylint: disable=arguments-differ
        kwargs.update({
            'build_env': self,
        })
        return super().run_command_class(*cmd, **kwargs)


class LocalBuildEnvironment(BuildEnvironment):

    """Local execution build environment."""

    command_class = BuildCommand


class DockerBuildEnvironment(BuildEnvironment):

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
    container_mem_limit = DOCKER_LIMITS.get('memory')
    container_time_limit = DOCKER_LIMITS.get('time')

    def __init__(self, *args, **kwargs):
        container_image = kwargs.pop('container_image', None)

        super().__init__(*args, **kwargs)
        self.client = None
        self.container = None
        self.container_name = self.get_container_name()

        # Decide what Docker image to use, based on priorities:
        # Use the Docker image set by our feature flag: ``testing`` or,
        if self.project.has_feature(Feature.USE_TESTING_BUILD_IMAGE):
            self.container_image = 'readthedocs/build:testing'
        # the image set by user or,
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

        if self.project.container_mem_limit:
            self.container_mem_limit = self.project.container_mem_limit
        if self.project.container_time_limit:
            self.container_time_limit = self.project.container_time_limit

        log.bind(
            project_slug=self.project.slug,
            version_slug=self.version.slug,
        )

        # NOTE: as this environment is used for `sync_repository_task` it may
        # not have a build associated
        if self.build:
            log.bind(
                build_id=self.build.get('id'),
            )

    def __enter__(self):
        """Start of environment context."""
        try:
            # Test for existing container. We remove any stale containers that
            # are no longer running here if there is a collision. We throw an
            # exception
            state = self.container_state()
            if state is not None:
                if state.get('Running') is True:
                    raise BuildAppError(
                        _(
                            'A build environment is currently '
                            'running for this version',
                        ),
                    )

                log.warning(
                    'Removing stale container.',
                    container_id=self.container_id,
                )
                client = self.get_client()
                client.remove_container(self.container_id)
        except (DockerAPIError, ConnectionError) as e:
            raise BuildAppError(e.explanation)

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
                'Container does not exists, nothing to kill.',
                container_id=self.container_id,
            )
        except DockerAPIError:
            # Logging this as warning because it usually happens due memory
            # limit or build timeout. In those cases, the container is not
            # running and can't be killed
            log.warning(
                'Unable to kill container.',
                container_id=self.container_id,
            )

        # Save the container's state before removing it to know what exception
        # to raise in the next step (`update_build_from_container_state`)
        state = self.container_state()

        try:
            log.info('Removing container.', container_id=self.container_id)
            client.remove_container(self.container_id)
        except DockerNotFoundError:
            log.info(
                'Container does not exists, nothing to remove.',
                container_id=self.container_id,
            )
        # Catch direct failures from Docker API or with an HTTP request.
        # These errors should not surface to the user.
        except (DockerAPIError, ConnectionError, ReadTimeout):
            log.exception("Couldn't remove container")

        self.raise_container_error(state)

    def get_container_name(self):
        if self.build:
            name = 'build-{build}-project-{project_id}-{project_name}'.format(
                build=self.build.get('id'),
                project_id=self.project.pk,
                project_name=self.project.slug,
            )
        else:
            # An uuid is added, so the container name is unique per sync.
            uuid_ = uuid.uuid4().hex[:8]
            name = f'sync-{uuid_}-project-{self.project.pk}-{self.project.slug}'
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
        except DockerException as e:
            raise BuildAppError(e.explanation)

    def _get_binds(self):
        """
        Return proper Docker Binds depending on settings.

        It uses Docker Volume if running on a docker-compose. Otherwise, it
        returns just a regular mountpoint path.
        """
        if getattr(settings, 'RTD_DOCKER_COMPOSE', False):
            from pathlib import Path
            binds = {
                settings.RTD_DOCKER_COMPOSE_VOLUME: {
                    'bind': str(Path(self.project.doc_path).parent),
                    'mode': 'rw',
                },
            }
        else:
            binds = {
                self.project.doc_path: {
                    'bind': self.project.doc_path,
                    'mode': 'rw',
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
            return self.container.get('Id')

    def container_state(self):
        """Get container state."""
        client = self.get_client()
        try:
            info = client.inspect_container(self.container_id)
            return info.get('State', {})
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
        if state is not None and state.get('Running') is False:
            if state.get('ExitCode') == DOCKER_TIMEOUT_EXIT_CODE:
                raise BuildUserError(
                    _('Build exited due to time out'),
                )

            if state.get('OOMKilled', False):
                raise BuildUserError(
                    _('Build exited due to excessive memory consumption'),
                )

            if state.get('Error'):
                raise BuildAppError(
                    (
                        _('Build exited due to unknown error: {0}')
                        .format(state.get('Error')),
                    )
                )

    def create_container(self):
        """Create docker container."""
        client = self.get_client()
        try:
            docker_runtime = self.project.get_feature_value(
                Feature.DOCKER_GVISOR_RUNTIME,
                positive="runsc",
                negative=None,
            )
            log.info(
                'Creating Docker container.',
                container_image=self.container_image,
                container_id=self.container_id,
                docker_runtime=docker_runtime,
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
                runtime=docker_runtime,
            )
            client.start(container=self.container_id)
        except (DockerAPIError, ConnectionError) as e:
            raise BuildAppError(e.explanation)
