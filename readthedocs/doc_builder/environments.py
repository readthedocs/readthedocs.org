"""Documentation Builder Environments"""

from __future__ import absolute_import
from builtins import str
from builtins import object
import os
import re
import sys
import logging
import subprocess
import traceback
import socket
from datetime import datetime

from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from docker import Client
from docker.utils import create_host_config
from docker.errors import APIError as DockerAPIError, DockerException
from slumber.exceptions import HttpClientError

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import BuildCommandResultMixin
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.api.client import api as api_v1
from readthedocs.restapi.client import api as api_v2

from .exceptions import (BuildEnvironmentException, BuildEnvironmentError,
                         BuildEnvironmentWarning)
from .constants import (DOCKER_SOCKET, DOCKER_VERSION, DOCKER_IMAGE,
                        DOCKER_LIMITS, DOCKER_TIMEOUT_EXIT_CODE,
                        DOCKER_OOM_EXIT_CODE, SPHINX_TEMPLATE_DIR,
                        MKDOCS_TEMPLATE_DIR, DOCKER_HOSTNAME_MAX_LEN)
import six

log = logging.getLogger(__name__)


__all__ = (
    'api_v1', 'api_v2',
    'BuildCommand', 'DockerBuildCommand',
    'BuildEnvironment', 'LocalEnvironment', 'DockerEnvironment',
)


class BuildCommand(BuildCommandResultMixin):

    """Wrap command execution for execution in build environments

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
                 bin_path=None, description=None):
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
        self.exit_code = None

    def __str__(self):
        # TODO do we want to expose the full command here?
        output = u''
        if self.output is not None:
            output = self.output.encode('utf-8')
        return '\n'.join([self.get_command(), output])

    def run(self):
        """Set up subprocess and execute command

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
            try:
                self.output = cmd_stdout.decode('utf-8', 'replace')
            except (TypeError, AttributeError):
                self.output = None
            try:
                self.error = cmd_stderr.decode('utf-8', 'replace')
            except (TypeError, AttributeError):
                self.error = None
            self.exit_code = proc.returncode
        except OSError:
            self.error = traceback.format_exc()
            self.output = self.error
            self.exit_code = -1
        finally:
            self.end_time = datetime.utcnow()

    def get_command(self):
        """Flatten command"""
        if hasattr(self.command, '__iter__') and not isinstance(self.command, str):
            return ' '.join(self.command)
        return self.command

    def save(self):
        """Save this command and result via the API"""
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

    """Create a docker container and run a command inside the container

    Build command to execute in docker container
    """

    def run(self):
        """Execute command in existing Docker container

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        """
        log.info("Running in container %s: '%s' [%s]",
                 self.build_env.container_id, self.get_command(), self.cwd)

        self.start_time = datetime.utcnow()
        client = self.build_env.get_client()
        try:
            exec_cmd = client.exec_create(
                container=self.build_env.container_id,
                cmd=self.get_wrapped_command(),
                stdout=True,
                stderr=True
            )

            output = client.exec_start(exec_id=exec_cmd['Id'], stream=False)
            try:
                self.output = output.decode('utf-8', 'replace')
            except (TypeError, AttributeError):
                self.output = ''
            cmd_ret = client.exec_inspect(exec_id=exec_cmd['Id'])
            self.exit_code = cmd_ret['ExitCode']

            # Docker will exit with a special exit code to signify the command
            # was killed due to memory usage, make the error code nicer.
            if (self.exit_code == DOCKER_OOM_EXIT_CODE and
                    self.output == 'Killed\n'):
                self.output = _('Command killed due to excessive memory '
                                'consumption\n')
        except DockerAPIError:
            self.exit_code = -1
            if self.output is None or not self.output:
                self.output = _('Command exited abnormally')
        finally:
            self.end_time = datetime.utcnow()

    def get_wrapped_command(self):
        """Escape special bash characters in command to wrap in shell

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


class BuildEnvironment(object):

    """Base build environment

    Base class for wrapping command execution for build steps. This provides a
    context for command execution and reporting, and eventually performs updates
    on the build object itself, reporting success/failure, as well as top-level
    failures.

    :param project: Project that is being built
    :param version: Project version that is being built
    :param build: Build instance
    :param record: Record status of build object
    :param environment: shell environment variables
    """

    def __init__(self, project=None, version=None, build=None, record=True,
                 environment=None):
        self.project = project
        self.version = version
        self.build = build
        self.record = record
        self.environment = environment or {}

        self.commands = []
        self.failure = None
        self.start_time = datetime.utcnow()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        ret = self.handle_exception(exc_type, exc_value, tb)
        self.build['state'] = BUILD_STATE_FINISHED
        log.info(LOG_TEMPLATE
                 .format(project=self.project.slug,
                         version=self.version.slug,
                         msg='Build finished'))
        return ret

    def handle_exception(self, exc_type, exc_value, _):
        """Exception handling for __enter__ and __exit__

        This reports on the exception we're handling and special cases
        subclasses of BuildEnvironmentException.  For
        :py:class:`BuildEnvironmentWarning`, exit this context gracefully, but
        don't mark the build as a failure.  For all other exception classes,
        including :py:class:`BuildEnvironmentError`, the build will be marked as
        a failure and the context will be gracefully exited.
        """
        if exc_type is not None:
            log.error(LOG_TEMPLATE
                      .format(project=self.project.slug,
                              version=self.version.slug,
                              msg=exc_value),
                      exc_info=True)
            if not issubclass(exc_type, BuildEnvironmentWarning):
                self.failure = exc_value
            return True

    def run(self, *cmd, **kwargs):
        """Shortcut to run command from environment"""
        return self.run_command_class(cls=self.command_class, cmd=cmd, **kwargs)

    def run_command_class(self, cls, cmd, **kwargs):
        """Run command from this environment

        Use ``cls`` to instantiate a command

        :param warn_only: Don't raise an exception on command failure
        """
        warn_only = kwargs.pop('warn_only', False)
        # Remove PATH from env, and set it to bin_path if it isn't passed in
        env_path = self.environment.pop('BIN_PATH', None)
        if 'bin_path' not in kwargs and env_path:
            kwargs['bin_path'] = env_path
        assert 'environment' not in kwargs, "environment can't be passed in via commands."
        kwargs['environment'] = self.environment
        kwargs['build_env'] = self
        build_cmd = cls(cmd, **kwargs)
        self.commands.append(build_cmd)
        build_cmd.run()

        # Save to database
        if self.record:
            build_cmd.save()

        if build_cmd.failed:
            msg = u'Command {cmd} failed'.format(cmd=build_cmd.get_command())

            if build_cmd.output:
                msg += u':\n{out}'.format(out=build_cmd.output)

            if warn_only:
                log.warn(LOG_TEMPLATE
                         .format(project=self.project.slug,
                                 version=self.version.slug,
                                 msg=msg))
            else:
                raise BuildEnvironmentWarning(msg)
        return build_cmd

    @property
    def successful(self):
        """Is build completed, without top level failures or failing commands"""
        return (self.done and self.failure is None and
                all(cmd.successful for cmd in self.commands))

    @property
    def failed(self):
        """Is build completed, but has top level failure or failing commands"""
        return (self.done and (
            self.failure is not None or
            any(cmd.failed for cmd in self.commands)
        ))

    @property
    def done(self):
        """Is build in finished state"""
        return (self.build is not None and
                self.build['state'] == BUILD_STATE_FINISHED)

    def update_build(self, state=None):
        """Record a build by hitting the API

        This step is skipped if we aren't recording the build, or if we don't
        want to record successful builds yet (if we are running setup commands
        for the build)
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
            if self.failure and isinstance(self.failure,
                                           BuildEnvironmentException):
                self.build['exit_code'] = self.failure.status_code
            elif self.commands:
                self.build['exit_code'] = max([cmd.exit_code
                                               for cmd in self.commands])

        self.build['setup'] = self.build['setup_error'] = ""
        self.build['output'] = self.build['error'] = ""

        if self.start_time:
            build_length = (datetime.utcnow() - self.start_time)
            self.build['length'] = int(build_length.total_seconds())

        if self.failure is not None:
            # Only surface the error message if it was a
            # BuildEnvironmentException or BuildEnvironmentWarning
            if isinstance(self.failure,
                          (BuildEnvironmentException, BuildEnvironmentWarning)):
                self.build['error'] = str(self.failure)
            else:
                self.build['error'] = ugettext_noop(
                    "An unexpected error occurred")

        # Attempt to stop unicode errors on build reporting
        for key, val in list(self.build.items()):
            if isinstance(val, six.binary_type):
                self.build[key] = val.decode('utf-8', 'ignore')

        try:
            api_v2.build(self.build['id']).put(self.build)
        except HttpClientError as e:
            log.error("Unable to post a new build: %s", e.content)
        except Exception:
            log.error("Unknown build exception", exc_info=True)


class LocalEnvironment(BuildEnvironment):

    """Local execution environment"""

    command_class = BuildCommand


class DockerEnvironment(BuildEnvironment):

    """
    Docker build environment, uses docker to contain builds

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
        super(DockerEnvironment, self).__init__(*args, **kwargs)
        self.client = None
        self.container = None
        self.container_name = slugify(
            'build-{build}-project-{project_id}-{project_name}'.format(
                build=self.build.get('id'),
                project_id=self.project.pk,
                project_name=self.project.slug,
            )[:DOCKER_HOSTNAME_MAX_LEN]
        )
        if self.project.container_mem_limit:
            self.container_mem_limit = self.project.container_mem_limit
        if self.project.container_time_limit:
            self.container_time_limit = self.project.container_time_limit

    def __enter__(self):
        """Start of environment context"""
        log.info('Creating container')
        try:
            # Test for existing container. We remove any stale containers that
            # are no longer running here if there is a collision. If the
            # container is still running, this would be a failure of the version
            # locking code, so we throw an exception.
            state = self.container_state()
            if state is not None:
                if state.get('Running') is True:
                    exc = BuildEnvironmentError(
                        _('A build environment is currently '
                          'running for this version'))
                    self.failure = exc
                    self.build['state'] = BUILD_STATE_FINISHED
                    raise exc
                else:
                    log.warn(LOG_TEMPLATE
                             .format(
                                 project=self.project.slug,
                                 version=self.version.slug,
                                 msg=("Removing stale container {0}"
                                      .format(self.container_id))))
                    client = self.get_client()
                    client.remove_container(self.container_id)
        except DockerAPIError:
            pass

        # Create the checkout path if it doesn't exist to avoid Docker creation
        if not os.path.exists(self.project.doc_path):
            os.makedirs(self.project.doc_path)

        try:
            self.create_container()
        except:  # pylint: disable=broad-except
            self.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """End of environment context"""
        ret = self.handle_exception(exc_type, exc_value, tb)

        # Update buildenv state given any container error states first
        self.update_build_from_container_state()

        client = self.get_client()
        try:
            client.kill(self.container_id)
        except DockerAPIError:
            pass
        try:
            log.info('Removing container %s', self.container_id)
            client.remove_container(self.container_id)
        except DockerAPIError:
            log.error(LOG_TEMPLATE
                      .format(
                          project=self.project.slug,
                          version=self.version.slug,
                          msg="Couldn't remove container"),
                      exc_info=True)
        self.container = None
        self.build['state'] = BUILD_STATE_FINISHED
        log.info(LOG_TEMPLATE
                 .format(project=self.project.slug,
                         version=self.version.slug,
                         msg='Build finished'))
        return ret

    def get_client(self):
        """Create Docker client connection"""
        try:
            if self.client is None:
                self.client = Client(
                    base_url=self.docker_socket,
                    version=DOCKER_VERSION,
                    timeout=None
                )
            return self.client
        except DockerException as e:
            log.error(LOG_TEMPLATE
                      .format(
                          project=self.project.slug,
                          version=self.version.slug,
                          msg=e),
                      exc_info=True)
            raise BuildEnvironmentError('Problem creating build environment')

    @property
    def container_id(self):
        """Return id of container if it is valid"""
        if self.container_name:
            return self.container_name
        elif self.container:
            return self.container.get('Id')

    def container_state(self):
        """Get container state"""
        client = self.get_client()
        try:
            info = client.inspect_container(self.container_id)
            return info.get('State', {})
        except DockerAPIError:
            return None

    def update_build_from_container_state(self):
        """Update buildenv state from container state

        In the case of the parent command exiting before the exec commands
        finish and the container is destroyed, or in the case of OOM on the
        container, set a failure state and error message explaining the failure
        on the buildenv.
        """
        state = self.container_state()
        if state is not None and state.get('Running') is False:
            if state.get('ExitCode') == DOCKER_TIMEOUT_EXIT_CODE:
                self.failure = BuildEnvironmentError(
                    _('Build exited due to time out'))
            elif state.get('OOMKilled', False):
                self.failure = BuildEnvironmentError(
                    _('Build exited due to excessive memory consumption'))
            elif state.get('Error'):
                self.failure = BuildEnvironmentError(
                    (_('Build exited due to unknown error: {0}')
                     .format(state.get('Error'))))

    def create_container(self):
        """Create docker container"""
        client = self.get_client()
        image = self.container_image
        if self.project.container_image:
            image = self.project.container_image
        try:
            self.container = client.create_container(
                image=image,
                command=('/bin/sh -c "sleep {time}; exit {exit}"'
                         .format(time=self.container_time_limit,
                                 exit=DOCKER_TIMEOUT_EXIT_CODE)),
                name=self.container_id,
                hostname=self.container_id,
                host_config=create_host_config(binds={
                    SPHINX_TEMPLATE_DIR: {
                        'bind': SPHINX_TEMPLATE_DIR,
                        'mode': 'ro'
                    },
                    MKDOCS_TEMPLATE_DIR: {
                        'bind': MKDOCS_TEMPLATE_DIR,
                        'mode': 'ro'
                    },
                    self.project.doc_path: {
                        'bind': self.project.doc_path,
                        'mode': 'rw'
                    },
                }),
                detach=True,
                environment=self.environment,
                mem_limit=self.container_mem_limit,
            )
            client.start(container=self.container_id)
        except DockerAPIError as e:
            log.error(LOG_TEMPLATE
                      .format(
                          project=self.project.slug,
                          version=self.version.slug,
                          msg=e.explanation),
                      exc_info=True)
            raise BuildEnvironmentError('Build environment creation failed')
