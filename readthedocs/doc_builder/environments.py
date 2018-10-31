# -*- coding: utf-8 -*-

"""Documentation Builder Environments."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import os
import re
import socket
import subprocess
import sys
import traceback
from datetime import datetime

import six
from builtins import object, str
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from docker import APIClient
from docker.errors import APIError as DockerAPIError
from docker.errors import DockerException
from requests.exceptions import ConnectionError
from slumber.exceptions import HttpClientError

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import BuildCommandResultMixin
from readthedocs.core.utils import slugify
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.restapi.client import api as api_v2

from .constants import (
    DOCKER_HOSTNAME_MAX_LEN, DOCKER_IMAGE, DOCKER_LIMITS, DOCKER_OOM_EXIT_CODE,
    DOCKER_SOCKET, DOCKER_TIMEOUT_EXIT_CODE, DOCKER_VERSION,
    MKDOCS_TEMPLATE_DIR, SPHINX_TEMPLATE_DIR)
from .exceptions import (
    BuildEnvironmentCreationFailed, BuildEnvironmentError,
    BuildEnvironmentException, BuildEnvironmentWarning, BuildTimeoutError,
    ProjectBuildsSkippedError, VersionLockedError, YAMLParseError)

log = logging.getLogger(__name__)

__all__ = (
    'api_v2',
    'BuildCommand',
    'DockerBuildCommand',
    'LocalEnvironment',
    'LocalBuildEnvironment',
    'DockerBuildEnvironment',
)


class BuildCommand(BuildCommandResultMixin):

    """
    Wrap command execution for execution in build environments.

    This wraps subprocess commands with some logic to handle exceptions,
    logging, and setting up the env for the build command.

    This acts a mapping of sorts to the API representation of the
    :py:class:`readthedocs.builds.models.BuildCommandResult` model.

    :param command: string or array of command parameters
    :param cwd: current working path for the command
    :param shell: execute command in shell, default=False
    :param environment: environment variables to add to environment
    :type environment: dict
    :param combine_output: combine stdout/stderr, default=True
    :param input_data: data to pass in on stdin
    :type input_data: str
    :param build_env: build environment to use to execute commands
    :param bin_path: binary path to add to PATH resolution
    :param description: a more grokable description of the command being run
    """

    def __init__(self, command, cwd=None, shell=False, environment=None,
                 combine_output=True, input_data=None, build_env=None,
                 bin_path=None, description=None, record_as_success=False):
        self.command = command
        self.shell = shell
        if cwd is None:
            cwd = os.getcwd()
        self.cwd = cwd
        self.environment = os.environ.copy()
        if environment is not None:
            assert 'PATH' not in environment, "PATH can't be set"
            self.environment.update(environment)

        self.combine_output = combine_output
        self.input_data = input_data
        self.build_env = build_env
        self.output = None
        self.error = None
        self.start_time = None
        self.end_time = None

        self.bin_path = bin_path
        self.description = ''
        if description is not None:
            self.description = description
        self.record_as_success = record_as_success
        self.exit_code = None

    def __str__(self):
        # TODO do we want to expose the full command here?
        output = u''
        if self.output is not None:
            output = self.output.encode('utf-8')
        return '\n'.join([self.get_command(), output])

    def run(self):
        """
        Set up subprocess and execute command.

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        """
        log.info("Running: '%s' [%s]", self.get_command(), self.cwd)

        self.start_time = datetime.utcnow()
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        stdin = None
        if self.input_data is not None:
            stdin = subprocess.PIPE
        if self.combine_output:
            stderr = subprocess.STDOUT

        environment = {}
        environment.update(self.environment)
        environment['READTHEDOCS'] = 'True'
        if self.build_env is not None:
            environment['READTHEDOCS_VERSION'] = self.build_env.version.slug
            environment['READTHEDOCS_PROJECT'] = self.build_env.project.slug
        if 'DJANGO_SETTINGS_MODULE' in environment:
            del environment['DJANGO_SETTINGS_MODULE']
        if 'PYTHONPATH' in environment:
            del environment['PYTHONPATH']
        if self.bin_path is not None:
            env_paths = environment.get('PATH', '').split(':')
            env_paths.insert(0, self.bin_path)
            environment['PATH'] = ':'.join(env_paths)

        try:
            proc = subprocess.Popen(
                self.command,
                shell=self.shell,
                cwd=self.cwd,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=environment,
            )
            cmd_input = None
            if self.input_data is not None:
                cmd_input = self.input_data

            if isinstance(cmd_input, six.string_types):
                cmd_input_bytes = cmd_input.encode('utf-8')
            else:
                cmd_input_bytes = cmd_input
            cmd_output = proc.communicate(input=cmd_input_bytes)
            (cmd_stdout, cmd_stderr) = cmd_output
            self.output = self.sanitize_output(cmd_stdout)
            self.error = self.sanitize_output(cmd_stderr)
            self.exit_code = proc.returncode
        except OSError:
            self.error = traceback.format_exc()
            self.output = self.error
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
            'description': self.description,
            'output': self.output,
            'exit_code': self.exit_code,
            'start_time': self.start_time,
            'end_time': self.end_time,
        }
        api_v2.command.post(data)


class DockerBuildCommand(BuildCommand):

    """
    Create a docker container and run a command inside the container.

    Build command to execute in docker container
    """

    def run(self):
        """
        Execute command in existing Docker container.

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        """
        log.info(
            "Running in container %s: '%s' [%s]",
            self.build_env.container_id,
            self.get_command(),
            self.cwd,
        )

        self.start_time = datetime.utcnow()
        client = self.build_env.get_client()
        try:
            exec_cmd = client.exec_create(
                container=self.build_env.container_id,
                cmd=self.get_wrapped_command(),
                stdout=True,
                stderr=True,
            )

            cmd_output = client.exec_start(exec_id=exec_cmd['Id'], stream=False)
            self.output = self.sanitize_output(cmd_output)
            cmd_ret = client.exec_inspect(exec_id=exec_cmd['Id'])
            self.exit_code = cmd_ret['ExitCode']

            # Docker will exit with a special exit code to signify the command
            # was killed due to memory usage, make the error code
            # nicer. Sometimes the kernel kills the command and Docker doesn't
            # not use the specific exit code, so we check if the word `Killed`
            # is in the last 15 lines of the command's output
            killed_in_output = 'Killed' in '\n'.join(self.output.splitlines()[-15:])
            if self.exit_code == DOCKER_OOM_EXIT_CODE or (self.exit_code == 1 and killed_in_output):
                self.output = _('Command killed due to excessive memory '
                                'consumption\n')
        except DockerAPIError:
            self.exit_code = -1
            if self.output is None or not self.output:
                self.output = _('Command exited abnormally')
        finally:
            self.end_time = datetime.utcnow()

    def get_wrapped_command(self):
        """
        Escape special bash characters in command to wrap in shell.

        In order to set the current working path inside a docker container, we
        need to wrap the command in a shell call manually. Some characters will
        be interpreted as shell characters without escaping, such as: ``pip
        install requests<0.8``. This escapes a good majority of those
        characters.
        """
        bash_escape_re = re.compile(r"([\t\ \!\"\#\$\&\'\(\)\*\:\;\<\>\?\@"
                                    r"\[\\\]\^\`\{\|\}\~])")
        prefix = ''
        if self.bin_path:
            prefix += 'PATH={0}:$PATH '.format(self.bin_path)
        return ("/bin/sh -c 'cd {cwd} && {prefix}{cmd}'"
                .format(
                    cwd=self.cwd,
                    prefix=prefix,
                    cmd=(' '.join([bash_escape_re.sub(r'\\\1', part)
                                   for part in self.command]))))


class BaseEnvironment(object):

    """
    Base environment class.

    Used to run arbitrary commands outside a build.
    """

    def __init__(self, project, environment=None):
        # TODO: maybe we can remove this Project dependency also
        self.project = project
        self.environment = environment or {}
        self.commands = []

    def record_command(self, command):
        pass

    def run(self, *cmd, **kwargs):
        """Shortcut to run command from environment."""
        return self.run_command_class(cls=self.command_class, cmd=cmd, **kwargs)

    def run_command_class(
            self, cls, cmd, record=None, warn_only=False,
            record_as_success=False, **kwargs):
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
        if record is None:
            # ``self.record`` only exists when called from ``*BuildEnvironment``
            record = getattr(self, 'record', False)

        if not record:
            warn_only = True

        if record_as_success:
            record = True
            warn_only = True
            # ``record_as_success`` is needed to instantiate the BuildCommand
            kwargs.update({'record_as_success': record_as_success})

        # Remove PATH from env, and set it to bin_path if it isn't passed in
        env_path = self.environment.pop('BIN_PATH', None)
        if 'bin_path' not in kwargs and env_path:
            kwargs['bin_path'] = env_path
        assert 'environment' not in kwargs, "environment can't be passed in via commands."
        kwargs['environment'] = self.environment

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
            msg = u'Command {cmd} failed'.format(cmd=build_cmd.get_command())

            if build_cmd.output:
                msg += u':\n{out}'.format(out=build_cmd.output)

            if warn_only:
                log.warning(LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version='latest',
                    msg=msg,
                ))
            else:
                raise BuildEnvironmentWarning(msg)
        return build_cmd


class LocalEnvironment(BaseEnvironment):

    # TODO: BuildCommand name doesn't make sense here, should be just Command
    command_class = BuildCommand


class BuildEnvironment(BaseEnvironment):

    """
    Base build environment.

    Base class for wrapping command execution for build steps. This provides a
    context for command execution and reporting, and eventually performs updates
    on the build object itself, reporting success/failure, as well as failures
    during the context manager enter and exit.

    Any exceptions raised inside this context and handled by the eventual
    :py:meth:`__exit__` method, specifically, inside :py:meth:`handle_exception`
    and :py:meth:`update_build`. If the exception is a subclass of
    :py:class:`BuildEnvironmentError`, then this error message is added to the
    build object and is shown to the user as the top-level failure reason for
    why the build failed. Other exceptions raise a general failure warning on
    the build.

    We only update the build through the API in one of three cases:

    * The build is not done and needs an additional build step to follow
    * The build failed and we should always report this change
    * The build was successful and ``update_on_success`` is ``True``

    :param project: Project that is being built
    :param version: Project version that is being built
    :param build: Build instance
    :param record: Record status of build object
    :param environment: shell environment variables
    :param update_on_success: update the build object via API if the build was
                              successful
    """

    # Exceptions considered ERROR from a Build perspective but as a WARNING for
    # the application itself. These exception are logged as warning and not sent
    # to Sentry.
    WARNING_EXCEPTIONS = (
        VersionLockedError,
        ProjectBuildsSkippedError,
        YAMLParseError,
        BuildTimeoutError,
    )

    def __init__(self, project=None, version=None, build=None, config=None,
                 record=True, environment=None, update_on_success=True):
        super(BuildEnvironment, self).__init__(project, environment)
        self.version = version
        self.build = build
        self.config = config
        self.record = record
        self.update_on_success = update_on_success

        self.failure = None
        self.start_time = datetime.utcnow()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        ret = self.handle_exception(exc_type, exc_value, tb)
        self.update_build(BUILD_STATE_FINISHED)
        log.info(
            LOG_TEMPLATE.format(
                project=self.project.slug,
                version=self.version.slug,
                msg='Build finished',
            )
        )
        return ret

    def handle_exception(self, exc_type, exc_value, _):
        """
        Exception handling for __enter__ and __exit__.

        This reports on the exception we're handling and special cases
        subclasses of BuildEnvironmentException. For
        :py:class:`BuildEnvironmentWarning`, exit this context gracefully, but
        don't mark the build as a failure. For all other exception classes,
        including :py:class:`BuildEnvironmentError`, the build will be marked as
        a failure and the context will be gracefully exited.

        If the exception's type is :py:class:`BuildEnvironmentWarning` or it's
        an exception marked as ``WARNING_EXCEPTIONS`` we log the problem as a
        WARNING, otherwise we log it as an ERROR.
        """
        if exc_type is not None:
            log_level_function = None
            if issubclass(exc_type, BuildEnvironmentWarning):
                log_level_function = log.warning
            elif exc_type in self.WARNING_EXCEPTIONS:
                log_level_function = log.warning
                self.failure = exc_value
            else:
                log_level_function = log.error
                self.failure = exc_value

            log_level_function(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg=exc_value,
                ),
                exc_info=True,
                extra={
                    'stack': True,
                    'tags': {
                        'build': self.build.get('id'),
                        'project': self.project.slug,
                        'version': self.version.slug,
                    },
                },
            )
            return True

    def record_command(self, command):
        command.save()

    def run(self, *cmd, **kwargs):
        kwargs.update({
            'build_env': self,
        })
        return super(BuildEnvironment, self).run(*cmd, **kwargs)

    def run_command_class(self, *cmd, **kwargs):  # pylint: disable=arguments-differ
        kwargs.update({
            'build_env': self,
        })
        return super(BuildEnvironment, self).run_command_class(*cmd, **kwargs)

    @property
    def successful(self):
        """Is build completed, without top level failures or failing commands."""  # noqa
        return (self.done and self.failure is None and
                all(cmd.successful for cmd in self.commands))

    @property
    def failed(self):
        """Is build completed, but has top level failure or failing commands."""
        return (self.done and (
            self.failure is not None or
            any(cmd.failed for cmd in self.commands)
        ))

    @property
    def done(self):
        """Is build in finished state."""
        return (self.build is not None and
                self.build['state'] == BUILD_STATE_FINISHED)

    def update_build(self, state=None):
        """
        Record a build by hitting the API.

        This step is skipped if we aren't recording the build. To avoid
        recording successful builds yet (for instance, running setup commands
        for the build), set the ``update_on_success`` argument to False on
        environment instantiation.

        If there was an error on the build, update the build regardless of
        whether ``update_on_success`` is ``True`` or not.
        """
        if not self.record:
            return None

        self.build['project'] = self.project.pk
        self.build['version'] = self.version.pk
        self.build['builder'] = socket.gethostname()
        self.build['state'] = state
        if self.done:
            self.build['success'] = self.successful

            # TODO drop exit_code and provide a more meaningful UX for error
            # reporting
            if self.failure and isinstance(
                    self.failure,
                    BuildEnvironmentException,
            ):
                self.build['exit_code'] = self.failure.status_code
            elif self.commands:
                self.build['exit_code'] = max([
                    cmd.exit_code for cmd in self.commands
                ])

        self.build['setup'] = self.build['setup_error'] = ''
        self.build['output'] = self.build['error'] = ''

        if self.start_time:
            build_length = (datetime.utcnow() - self.start_time)
            self.build['length'] = int(build_length.total_seconds())

        if self.failure is not None:
            # Surface a generic error if the class is not a
            # BuildEnvironmentError
            if not isinstance(
                    self.failure,
                    (
                        BuildEnvironmentException,
                        BuildEnvironmentWarning,
                    ),
            ):
                log.error(
                    'Build failed with unhandled exception: %s',
                    str(self.failure),
                    extra={
                        'stack': True,
                        'tags': {
                            'build': self.build.get('id'),
                            'project': self.project.slug,
                            'version': self.version.slug,
                        },
                    },
                )
                self.failure = BuildEnvironmentError(
                    BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                        build_id=self.build['id'],
                    ),
                )
            self.build['error'] = str(self.failure)

        # Attempt to stop unicode errors on build reporting
        for key, val in list(self.build.items()):
            if isinstance(val, six.binary_type):
                self.build[key] = val.decode('utf-8', 'ignore')

        # We are selective about when we update the build object here
        update_build = (
            # Build isn't done yet, we unconditionally update in this state
            not self.done
            # Build is done, but isn't successful, always update
            or (self.done and not self.successful)
            # Otherwise, are we explicitly to not update?
            or self.update_on_success
        )
        if update_build:
            try:
                api_v2.build(self.build['id']).put(self.build)
            except HttpClientError as e:
                log.exception(
                    'Unable to update build: id=%d',
                    self.build['id'],
                )
            except Exception:
                log.exception('Unknown build exception')


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

    :param docker_socket: Override to Docker socket URI
    """

    command_class = DockerBuildCommand
    container_image = DOCKER_IMAGE
    container_mem_limit = DOCKER_LIMITS.get('memory')
    container_time_limit = DOCKER_LIMITS.get('time')

    def __init__(self, *args, **kwargs):
        self.docker_socket = kwargs.pop('docker_socket', DOCKER_SOCKET)
        super(DockerBuildEnvironment, self).__init__(*args, **kwargs)
        self.client = None
        self.container = None
        self.container_name = slugify(
            'build-{build}-project-{project_id}-{project_name}'.format(
                build=self.build.get('id'),
                project_id=self.project.pk,
                project_name=self.project.slug,
            )[:DOCKER_HOSTNAME_MAX_LEN],
        )
        if self.config and self.config.build.image:
            self.container_image = self.config.build.image
        if self.project.container_image:
            self.container_image = self.project.container_image
        if self.project.container_mem_limit:
            self.container_mem_limit = self.project.container_mem_limit
        if self.project.container_time_limit:
            self.container_time_limit = self.project.container_time_limit

    def __enter__(self):
        """Start of environment context."""
        try:
            # Test for existing container. We remove any stale containers that
            # are no longer running here if there is a collision. If the
            # container is still running, this would be a failure of the version
            # locking code, so we throw an exception.
            state = self.container_state()
            if state is not None:
                if state.get('Running') is True:
                    exc = BuildEnvironmentError(
                        _(
                            'A build environment is currently '
                            'running for this version',
                        ),
                    )
                    self.failure = exc
                    self.build['state'] = BUILD_STATE_FINISHED
                    raise exc
                else:
                    log.warning(
                        LOG_TEMPLATE.format(
                            project=self.project.slug,
                            version=self.version.slug,
                            msg=(
                                'Removing stale container {0}'
                                .format(self.container_id)
                            ),
                        )
                    )
                    client = self.get_client()
                    client.remove_container(self.container_id)
        except (DockerAPIError, ConnectionError):
            # If there is an exception here, we swallow the exception as this
            # was just during a sanity check anyways.
            pass
        except BuildEnvironmentError:
            # There may have been a problem connecting to Docker altogether, or
            # some other handled exception here.
            self.__exit__(*sys.exc_info())
            raise

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
        try:
            # Update buildenv state given any container error states first
            self.update_build_from_container_state()

            client = self.get_client()
            try:
                client.kill(self.container_id)
            except DockerAPIError:
                log.exception(
                    'Unable to kill container: id=%s',
                    self.container_id,
                )
            try:
                log.info('Removing container: id=%s', self.container_id)
                client.remove_container(self.container_id)
            # Catch direct failures from Docker API or with a requests HTTP
            # request. These errors should not surface to the user.
            except (DockerAPIError, ConnectionError):
                log.exception(
                    LOG_TEMPLATE.format(
                        project=self.project.slug,
                        version=self.version.slug,
                        msg="Couldn't remove container",
                    ),
                )
            self.container = None
        except BuildEnvironmentError:
            # Several interactions with Docker can result in a top level failure
            # here. We'll catch this and report if there were no reported errors
            # already. These errors are not as important as a failure at deeper
            # code
            if not all([exc_type, exc_value, tb]):
                exc_type, exc_value, tb = sys.exc_info()

        return super(DockerBuildEnvironment, self).__exit__(exc_type, exc_value, tb)

    def get_client(self):
        """Create Docker client connection."""
        try:
            if self.client is None:
                self.client = APIClient(
                    base_url=self.docker_socket,
                    version=DOCKER_VERSION,
                )
            return self.client
        except DockerException as e:
            log.exception(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg='Could not connect to Docker API',
                ),
            )
            # We don't raise an error here mentioning Docker, that is a
            # technical detail that the user can't resolve on their own.
            # Instead, give the user a generic failure
            raise BuildEnvironmentError(
                BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                    build_id=self.build['id'],
                ),
            )

    def get_container_host_config(self):
        """
        Create the ``host_config`` settings for the container.

        It mainly generates the proper path bindings between the Docker
        container and the Host by mounting them with the proper permissions.
        Besides, it mounts the ``GLOBAL_PIP_CACHE`` if it's set and we are under
        ``DEBUG``.

        The object returned is passed to Docker function
        ``client.create_container``.
        """
        binds = {
            SPHINX_TEMPLATE_DIR: {
                'bind': SPHINX_TEMPLATE_DIR,
                'mode': 'ro',
            },
            MKDOCS_TEMPLATE_DIR: {
                'bind': MKDOCS_TEMPLATE_DIR,
                'mode': 'ro',
            },
            self.project.doc_path: {
                'bind': self.project.doc_path,
                'mode': 'rw',
            },
        }

        if getattr(settings, 'GLOBAL_PIP_CACHE', False) and settings.DEBUG:
            binds.update({
                self.project.pip_cache_path: {
                    'bind': self.project.pip_cache_path,
                    'mode': 'rw',
                },
            })
        return self.get_client().create_host_config(
            binds=binds,
            mem_limit=self.container_mem_limit,
        )

    @property
    def image_hash(self):
        """Return the hash of the Docker image."""
        client = self.get_client()
        image_metadata = client.inspect_image(self.container_image)
        return image_metadata.get('Id')

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

    def update_build_from_container_state(self):
        """
        Update buildenv state from container state.

        In the case of the parent command exiting before the exec commands
        finish and the container is destroyed, or in the case of OOM on the
        container, set a failure state and error message explaining the failure
        on the buildenv.
        """
        state = self.container_state()
        if state is not None and state.get('Running') is False:
            if state.get('ExitCode') == DOCKER_TIMEOUT_EXIT_CODE:
                self.failure = BuildEnvironmentError(
                    _('Build exited due to time out'),
                )
            elif state.get('OOMKilled', False):
                self.failure = BuildEnvironmentError(
                    _('Build exited due to excessive memory consumption'),
                )
            elif state.get('Error'):
                self.failure = BuildEnvironmentError((
                    _('Build exited due to unknown error: {0}')
                    .format(state.get('Error'))
                ),
                )

    def create_container(self):
        """Create docker container."""
        client = self.get_client()
        try:
            log.info(
                'Creating Docker container: image=%s',
                self.container_image,
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
                environment=self.environment,
            )
            client.start(container=self.container_id)
        except ConnectionError as e:
            log.exception(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg=(
                        'Could not connect to the Docker API, '
                        'make sure Docker is running'
                    ),
                ),
            )
            # We don't raise an error here mentioning Docker, that is a
            # technical detail that the user can't resolve on their own.
            # Instead, give the user a generic failure
            raise BuildEnvironmentError(
                BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
                    build_id=self.build['id'],
                ),
            )
        except DockerAPIError as e:
            log.exception(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg=e.explanation,
                ),
            )
            raise BuildEnvironmentCreationFailed
