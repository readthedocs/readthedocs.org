'''
Documentation Builder Environments
'''

import os
import re
import sys
import json
import logging
import subprocess
import traceback
import datetime
import socket

from django.utils.text import slugify
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from docker import Client
from docker.utils import create_host_config
from docker import errors as docker_errors

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.projects.utils import run
from readthedocs.restapi.serializers import VersionFullSerializer
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.api.client import api as api_v1

from .exceptions import BuildEnvironmentError


log = logging.getLogger(__name__)

DOCKER_SOCKET = getattr(settings, 'DOCKER_SOCKET', 'unix:///var/run/docker.sock')
DOCKER_VERSION = getattr(settings, 'DOCKER_VERSION', 'auto')
DOCKER_IMAGE = getattr(settings, 'DOCKER_IMAGE', 'rtfd-build')
DOCKER_MEM_LIMIT = '200m'


class BuildCommand(object):
    '''Wrap command execution for execution in build environments

    This wraps subprocess commands with some logic to handle exceptions,
    logging, and setting up the env for the build command.

    :param command: string or array of command parameters
    :param cwd: current working path
    :param shell: execute command in shell, default=True
    :param environment: environment variables to add to environment
    '''

    # TODO add short name here for reporting
    def __init__(self, command, cwd=None, shell=False, environment=None,
                 combine_output=True, input_data=None, build_env=None):
        self.command = command
        self.shell = shell
        if cwd is None:
            cwd = os.getcwd()
        self.cwd = cwd
        self.environment = os.environ.copy()
        if environment is not None:
            self.environment.update(environment)
        self.combine_output = combine_output
        self.build_env = build_env
        self.status = None
        self.input_data = input_data
        self.output = None
        self.error = None

    def __str__(self):
        # TODO do we want to expose the full command here?
        return '\n'.join([self.get_command(), self.output])

    def run(self):
        '''Set up subprocess and execute command

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        '''
        log.info("Running: '%s' [%s]", self.get_command(), self.cwd)

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
        if 'DJANGO_SETTINGS_MODULE' in environment:
            del environment['DJANGO_SETTINGS_MODULE']
        if 'PYTHONPATH' in environment:
            del environment['PYTHONPATH']

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
            cmd_output = proc.communicate(input=cmd_input)
            (self.output, self.error) = cmd_output
            self.status = proc.returncode
        except OSError:
            self.error = traceback.format_exc()
            self.output = self.error
            self.status = -1

    def get_command(self):
        '''Flatten command'''
        if hasattr(self.command, '__iter__'):
            return ' '.join(self.command)
        else:
            return self.command

    @property
    def successful(self):
        return self.status is not None and self.status == 0

    @property
    def failed(self):
        return self.status is not None and self.status != 0


class DockerBuildCommand(BuildCommand):
    '''Create a docker container and run a command inside the container

    Build command to execute in docker container
    '''

    def run(self, cmd_input=None, combine_output=True):
        '''Execute command in existing Docker container

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        '''
        log.info("Running in container %s: '%s' [%s]",
                 self.build_env.container_id, self.get_command(), self.cwd)

        client = self.build_env.get_client()
        exec_cmd = client.exec_create(
            container=self.build_env.container_id,
            cmd=self.get_wrapped_command(),
            stdout=True,
            stderr=True
        )

        # TODO split up stdout/stderr
        self.output = client.exec_start(exec_id=exec_cmd['Id'], stream=False)

        cmd_ret = client.exec_inspect(exec_id=exec_cmd['Id'])
        self.status = cmd_ret['ExitCode']

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
        return ("/bin/sh -c 'cd {cwd} && {cmd}'"
                .format(
                    cwd=self.cwd,
                    cmd=(' '.join([bash_escape_re.sub(r'\\\1', part)
                                   for part in self.command]))))


class EnvironmentBase(object):
    '''
    Base build environment

    Placeholder for reorganizing command execution.

    :param project: Project that is being built
    :param version: Project version that is being built
    :param build: Build instance
    :param record: Record status of build object
    '''

    def __init__(self, project=None, version=None, build=None, record=True):
        self.project = project
        self.version = version
        self.build = build
        self.record = record
        self.steps = []
        self.commands = []
        self.start_time = datetime.datetime.utcnow()
        self.state = None

    def __enter__(self):
        self.state = None
        return self

    def __exit__(self, exc_type, exc_value, tb):
        ret = None
        if exc_type is not None:
            log.error(
                LOG_TEMPLATE.format(
                    project=self.project.slug,
                    version=self.version.slug,
                    msg=exc_value),
                exc_info=True
            )
            # TODO maybe catch a warning exception here, and just pass that
            # through some how?
            if issubclass(exc_type, BuildEnvironmentError):
                ret = True
        # TODO this should be one call or the other man
        self.state = BUILD_STATE_FINISHED
        self.update_build(state=BUILD_STATE_FINISHED)
        log.info(LOG_TEMPLATE.format(project=self.project.slug,
                                     version=self.version.slug,
                                     msg='Build finished'))
        return ret

    def run(self, *cmd, **kwargs):
        '''Run command'''
        kwargs['build_env'] = self
        cmd = self.command_class(cmd, **kwargs)
        self.commands.append(cmd)
        cmd.run()
        # TODO handle this better, it should add some more information or
        # maybe be a command output class
        if cmd.failed:
            # TODO drop second line here if there is no output
            msg = 'Command {cmd} failed'.format(cmd=cmd.get_command())

            if cmd.output:
                msg += ':\n{out}'.format()
            raise BuildEnvironmentError('Command {cmd} failed:\n{out}'.format(
                cmd=cmd.get_command(),
                out=cmd.output
            ))
        return cmd

    @property
    def successful(self):
        return all(cmd.successful for cmd in self.commands)

    @property
    def failed(self):
        return any(cmd.failed for cmd in self.commands)

    @property
    def done(self):
        return self.state == BUILD_STATE_FINISHED

    def update_build(self, state=None):
        """
        Record a build by hitting the API.

        Returns nothing
        """
        if not self.record:
            return None

        self.build['builder'] = socket.gethostname()
        self.build['state'] = state
        if self.done:
            self.build['success'] = self.successful

        # TODO make this more intelligent, inspect all the steps here for failed
        # I mean, really, this should be an intelligent error code that we can
        # surface in the UI somehow, not just a meaningless number. Lets rather
        # make this some mechanism that the front end can easily translate.
        # XXX self.build['exit_code'] = max([results.get(step, [0])[0] for step in all_steps])
        self.build['exit_code'] = 1
        #

        self.build['setup'] = self.build['setup_error'] = ""
        self.build['output'] = self.build['error'] = ""

        if self.start_time:
            build_length = (datetime.datetime.utcnow() - self.start_time)
            self.build['length'] = build_length.total_seconds()

        # TODO Replace this with per-command output tracking in the db
        self.build['output'] = '\n'.join([str(cmd)
                                        for cmd in self.commands
                                        if cmd is not None])

        # Attempt to stop unicode errors on build reporting
        for key, val in self.build.items():
            if isinstance(val, basestring):
                self.build[key] = val.decode('utf-8', 'ignore')

        try:
            api_v1.build(self.build['id']).put(self.build)
        except Exception:
            log.error("Unable to post a new build", exc_info=True)


class LocalEnvironment(EnvironmentBase):
    '''Local execution environment'''
    command_class = BuildCommand


class DockerEnvironment(EnvironmentBase):
    '''
    Docker build environment, uses docker to contain builds

    If :py:data:`settings.DOCKER_ENABLE` is true, build documentation inside a
    docker container, instead of the host system, using this build environment
    class.  The build command creates a docker container from a pre-built image,
    defined by :py:data:`settings.DOCKER_IMAGE`.  This container is started with
    a mount to the project's build path under ``user_builds`` on the host
    machine, walling off project builds from reading/writing other projects'
    data.

    :param docker_socket: Override to Docker socket URI
    '''
    command_class = DockerBuildCommand
    container_image = DOCKER_IMAGE
    container_mem_limit = DOCKER_MEM_LIMIT

    def __init__(self, *args, **kwargs):
        self.docker_socket = kwargs.pop('docker_socket', DOCKER_SOCKET)
        super(DockerEnvironment, self).__init__(*args, **kwargs)
        self.client = None
        self.container = None
        self.container_name = None
        if self.version:
            self.container_name = slugify(unicode(self.version))

    def __enter__(self):
        '''Start of environment context'''
        log.info('Creating container')
        try:
            self.create_container()
        except (BuildEnvironmentError, docker_errors.APIError):
            # TODO replace this with an internal exception. We should handle our
            # own exceptions differently here.
            if self.__exit__(*sys.exc_info()):
                pass
            else:
                # TODO this should definitely do something to set an error state
                # on the buildenv or build. If this is triggered during
                # __enter__, there won't be any commands. Maybe we mock out
                # commands here instead?
                raise
        return self

    def __exit__(self, exc_type, exc_value, tb):
        '''End of environment context'''
        # TODO this should all provide some error checking or exception
        # handling. we don't know if the container will exist at this point.
        # Killing and removing might be mull operations that trigger 404 errors
        ret = super(DockerEnvironment, self).__exit__(exc_type, exc_value, tb)
        log.info('Removing container %s', self.container_id)
        client = self.get_client()
        client.kill(self.container_id)
        client.remove_container(self.container_id)
        self.container = None
        return ret

    def get_client(self):
        '''Create Docker client connection'''
        # TODO catch exceptions here
        if self.client is None:
            self.client = Client(
                base_url=self.docker_socket,
                version=DOCKER_VERSION
            )
        return self.client

    @property
    def container_id(self):
        '''Return id of container if it is valid'''
        if self.container_name is not None:
            return self.container_name
        elif self.container is not None:
            return self.container.get('Id')

    def create_container(self):
        '''
        Create docker container
        '''
        client = self.get_client()
        # TODO check self.version more here or in __init__
        # TODO this should check for a missing image first
        # TODO this should catch failures and pass a better exception to the
        # task processor
        try:
            self.container = client.create_container(
                image=self.container_image,
                command='/bin/sleep 600',
                name=self.container_id,
                hostname=self.container_id,
                host_config=create_host_config(binds={
                    self.project.doc_path: {
                        'bind': self.project.doc_path,
                        'mode': 'rw'
                    }
                }),
                detach=True,
                mem_limit=self.container_mem_limit,
            )
            started = client.start(container=self.container_id)
        except docker_errors.APIError as e:
            log.error(LOG_TEMPLATE
                      .format(
                          project=self.project.slug,
                          version=self.version.slug,
                          msg=e.explanation),
                      exc_info=True)
            raise BuildEnvironmentError('Build environment creation failed')
