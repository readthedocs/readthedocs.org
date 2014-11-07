'''
Documentation Builder Environments
'''

import os
import json
import logging
import subprocess
import traceback

from django.utils.text import slugify
from django.conf import settings
from rest_framework.renderers import JSONRenderer

from projects.utils import run
from restapi.serializers import VersionFullSerializer

log = logging.getLogger(__name__)


class EnvironmentBase(object):
    '''
    Base build environment

    Placeholder for reorganizing command execution.

    :param version: Project version that is being built
    '''

    def __init__(self, version):
        self.version = version

    def response(self, cmd, step='doc_builder'):
        '''Render a response for reporting to the build command page

        :param cmd:
            :py:class:`BuildCommand` instance after executing run, or dict
            containing the same keys to mock a cmd response.

        :param step:
            Result step for output page

        .. note:: In the future, this should return an actual object, or handle
            organizing command return to the API on a per-command basis.

        '''
        resp = {'status': None, 'output': None, 'error': None}
        for key in resp.keys():
            try:
                resp[key] = getattr(cmd, key)
            except AttributeError:
                try:
                    resp[key] = cmd[key]
                except KeyError:
                    pass
        return {step: (resp['status'], resp['output'], resp['error'])}


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

    :param version: Project version to be building
    '''

    def container_id(self):
        '''
        Container ID used in creating and destroying docker images
        '''
        return slugify(unicode(self.version))

    def build(self):
        '''
        Run build command in container

        This serializes the version object into JSON, which is passed through
        Docker, into :py:mod:`readthedocs.core.management.commands.run_docker`.
        This management command reads the JSON on STDIN, and builds a mocked up
        version object to pass around the build process.  After the build
        process, JSON is output on STDOUT and read by this command, converting
        it back into a results dictionary.

        We also set environment settings to pass into the docker command, for
        overriding settings in the subprocess django instance inside the
        container.

        .. note:: This is a temporary hack.
            We shouldn't need to pass JSON back and forth, but cutting off all
            access to API and Celery is a necessary part of containing builds.
            In the future, builds should happen in a contained environment like
            LXC or Docker containers, but this code should managed build state
            outside the process, eliminating the need for IPC of any kind.

        '''
        cmd = DockerBuildCommand(
            ['/home/docs/bin/python',
             '/home/docs/checkouts/readthedocs.org/readthedocs/manage.py',
             'run_docker',
             '--settings=settings.docker'],
            name=self.container_id(),
            environment=self.env_settings(),
            mounts=[(self.version.project.doc_path,
                     ('/home/docs/checkouts/readthedocs.org/'
                      'user_builds/{project}'
                      .format(project=self.version.project.slug)))]
        )
        with cmd:
            try:
                renderer = JSONRenderer()
                version_data = VersionFullSerializer(self.version).data
                cmd.run(cmd_input=renderer.render(version_data))
            except Exception as e:
                log.error('Passing data to Docker failed: %s', str(e))
                return self.response({'status': -1, 'output': None,
                                      'error': str(e)})
            if cmd.failed():
                log.error('Docker build command failed: %s', cmd.error)
                return self.response(cmd)
            else:
                # TODO when refactoring build output, just return the command
                # here. Or report the command output directly here.
                try:
                    # Using stdin/stdout as a bus, we're expecting JSON back on
                    # stdout here
                    return json.loads(cmd.output)
                except Exception as e:
                    log.error('Problem passing data to Docker build command: %s',
                              str(e))
                    return self.response({'status': -1, 'output': None,
                                          'error': str(e)})

    def env_settings(self):
        '''Return local django settings as environment variables

        This is used when passing in env variables to the subprocess management
        command, instead of requiring docker containers have a settings file
        installed with each build of the docker image.

        .. warning:: Never, ever, pass secure data as an evironment variable.
        '''
        env = {}
        for key in ['SLUMBER_API_HOST', 'PRODUCTION_DOMAIN']:
            val = getattr(settings, key)
            env['RTD_DOCKER_{0}'.format(key)] = val
        return env


class BuildCommand(object):
    '''Wrap command execution for execution in build environments

    This wraps subprocess commands with some logic to handle exceptions,
    logging, and setting up the env for the build command.

    :param command: string or array of command parameters
    :param cwd: current working path
    :param shell: execute command in shell, default=True
    :param environment: environment variables to add to environment
    '''

    def __init__(self, command, cwd=None, shell=True, environment=None):
        self.command = command
        self.shell = shell
        if cwd is None:
            cwd = os.getcwd()
        self.cwd = cwd
        self.environment = os.environ.copy()
        if environment is not None:
            self.environment.update(environment)
        self.status = None
        self.output = None
        self.error = None

    def __enter__(self):
        '''Set up local env vars for Python/Django'''
        environment = {}
        environment['READTHEDOCS'] = 'True'
        if 'DJANGO_SETTINGS_MODULE' in environment:
            del environment['DJANGO_SETTINGS_MODULE']
        if 'PYTHONPATH' in environment:
            del environment['PYTHONPATH']
        self.environment.update(environment)

    def __exit__(self, exc_type, exc_value, tb):
        '''Intercept exceptions for logging and let exception pass through'''
        if exc_type is not None:
            self.output = ''
            self.error = traceback.format_exc()
            self.status = -1
            log.error('Command execution failed: %s', self.get_command(),
                      exc_info=True)

    def run(self, cmd_input=None, combine_output=False):
        '''Set up subprocess and execute command

        :param cmd_input: input to pass to command in STDIN
        :type cmd_input: str
        :param combine_output: combine STDERR into STDOUT
        '''
        log.info("Running: '%s' [%s]", self.get_command(), self.cwd)

        stdin = None
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        if cmd_input is not None:
            stdin = subprocess.PIPE
        if combine_output:
            stderr = subprocess.STDOUT
        proc = subprocess.Popen(
            self.get_command(),
            shell=self.shell,
            cwd=self.cwd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=self.environment,
        )
        cmd_output = proc.communicate(cmd_input)
        (self.output, self.error) = cmd_output
        self.status = proc.returncode

    def get_command(self):
        '''Flatten command'''
        if isinstance(self.command, list):
            return ' '.join(self.command)
        else:
            return self.command

    def successful(self):
        return self.status is not None and self.status == 0

    def failed(self):
        return self.status is not None and self.status != 0


class DockerBuildCommand(BuildCommand):
    '''Create a docker container and run a command inside the container

    Build command to execute in docker container

    :param command:
        Command to run as a string or a lists of strings to be joined as
        space-separated.

    :param image:
        Docker image to run a container from. This is set in settings as well

    :param mounts:
        List of tuples defining pairs of paths to be mounted, the first
        element should be the host path, the second should be the
        container's path.

    :param user:
        User to run command as

    :param name:
        Container name

    :param remove:
        Automatically remove container after container command exits
    '''

    def __init__(self, command, image=None, mounts=None, name=None, remove=True,
                 user=None, environment=None, **kwargs):
        self.command = command
        self.image = image
        if mounts is None:
            mounts = []
        self.mounts = mounts
        self.name = name
        self.remove = remove
        self.user = user
        if environment is None:
            environment = {}
        self.docker_environment = environment
        super(DockerBuildCommand, self).__init__(command, **kwargs)

    def __enter__(self):
        if self.image is None:
            self.image = settings.DOCKER_IMAGE or 'rtfd-build'

        # Build docker command to wrap command
        docker_cmd = ['docker', 'run', '-i']
        for (env_key, env_val) in self.docker_environment.items():
            docker_cmd.extend(['-e', '"{key}={val}"'.format(key=env_key,
                                                            val=env_val)])

        try:
            for (path, mount_path) in self.mounts:
                docker_cmd.extend(['-v', ':'.join([path, mount_path])])
        except TypeError:
            log.warn('Invalid Docker volume mount specification')
        if self.name is not None:
            docker_cmd.append('--name={0}'.format(self.name))
        if self.user is not None:
            docker_cmd.append('--user={0}'.format(self.user))
        if self.remove:
            docker_cmd.append('--rm=true')

        # Add actual command finally
        docker_cmd.append(self.image)
        docker_cmd.append(self.get_command())
        self.command = docker_cmd
