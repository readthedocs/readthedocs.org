# -*- coding: utf-8 -*-
"""An abstraction over virtualenv and Conda environments."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import itertools
import json
import logging
import os
import shutil
from builtins import object, open

import six
from django.conf import settings

from readthedocs.doc_builder.config import load_yaml_config
from readthedocs.doc_builder.constants import DOCKER_IMAGE
from readthedocs.doc_builder.environments import DockerBuildEnvironment
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.projects.constants import LOG_TEMPLATE
from readthedocs.projects.models import Feature

log = logging.getLogger(__name__)


class PythonEnvironment(object):

    """An isolated environment into which Python packages can be installed."""

    def __init__(self, version, build_env, config=None):
        self.version = version
        self.project = version.project
        self.build_env = build_env
        if config:
            self.config = config
        else:
            self.config = load_yaml_config(version)
        # Compute here, since it's used a lot
        self.checkout_path = self.project.checkout_path(self.version.slug)

    def delete_existing_build_dir(self):
        # Handle deleting old build dir
        build_dir = os.path.join(
            self.venv_path(),
            'build')
        if os.path.exists(build_dir):
            log.info(LOG_TEMPLATE.format(
                project=self.project.slug,
                version=self.version.slug,
                msg='Removing existing build directory',
            ))
            shutil.rmtree(build_dir)

    def delete_existing_venv_dir(self):
        venv_dir = self.venv_path()
        # Handle deleting old venv dir
        if os.path.exists(venv_dir):
            log.info(LOG_TEMPLATE.format(
                project=self.project.slug,
                version=self.version.slug,
                msg='Removing existing venv directory',
            ))
            shutil.rmtree(venv_dir)

    def install_package(self):
        if (self.config.python.install_with_pip or
                getattr(settings, 'USE_PIP_INSTALL', False)):
            extra_req_param = ''
            if self.config.python.extra_requirements:
                extra_req_param = '[{0}]'.format(
                    ','.join(self.config.python.extra_requirements)
                )
            self.build_env.run(
                'python',
                self.venv_bin(filename='pip'),
                'install',
                '--ignore-installed',
                '--cache-dir',
                self.project.pip_cache_path,
                '.{0}'.format(extra_req_param),
                cwd=self.checkout_path,
                bin_path=self.venv_bin(),
            )
        elif self.config.python.install_with_setup:
            self.build_env.run(
                'python',
                'setup.py',
                'install',
                '--force',
                cwd=self.checkout_path,
                bin_path=self.venv_bin(),
            )

    def venv_bin(self, filename=None):
        """
        Return path to the virtualenv bin path, or a specific binary.

        :param filename: If specified, add this filename to the path return
        :returns: Path to virtualenv bin or filename in virtualenv bin
        """
        parts = [self.venv_path(), 'bin']
        if filename is not None:
            parts.append(filename)
        return os.path.join(*parts)

    def environment_json_path(self):
        """Return the path to the ``readthedocs-environment.json`` file."""
        return os.path.join(
            self.venv_path(),
            'readthedocs-environment.json',
        )

    @property
    def is_obsolete(self):
        """
        Determine if the environment is obsolete for different reasons.

        It checks the the data stored at ``readthedocs-environment.json`` and
        compares it with the one to be used. In particular:

        * the Python version (e.g. 2.7, 3, 3.6, etc)
        * the Docker image name
        * the Docker image hash

        :returns: ``True`` when it's obsolete and ``False`` otherwise

        :rtype: bool
        """
        # Always returns False if we don't have information about what Python
        # version/Docker image was used to create the venv as backward
        # compatibility.
        if not os.path.exists(self.environment_json_path()):
            return False

        try:
            with open(self.environment_json_path(), 'r') as fpath:
                environment_conf = json.load(fpath)
        except (IOError, TypeError, KeyError, ValueError):
            log.warning('Unable to read/parse readthedocs-environment.json file')
            # We remove the JSON file here to avoid cycling over time with a
            # corrupted file.
            os.remove(self.environment_json_path())
            return True

        env_python = environment_conf.get('python', {})
        env_build = environment_conf.get('build', {})

        # By defaulting non-existent options to ``None`` we force a wipe since
        # we don't know how the environment was created
        env_python_version = env_python.get('version', None)
        env_build_image = env_build.get('image', None)
        env_build_hash = env_build.get('hash', None)

        if isinstance(self.build_env, DockerBuildEnvironment):
            build_image = self.config.build.image or DOCKER_IMAGE
            image_hash = self.build_env.image_hash
        else:
            # e.g. LocalBuildEnvironment
            build_image = None
            image_hash = None

        # If the user define the Python version just as a major version
        # (e.g. ``2`` or ``3``) we won't know exactly which exact version was
        # used to create the venv but we can still compare it against the new
        # one coming from the project version config.
        return any([
            env_python_version != self.config.python_full_version,
            env_build_image != build_image,
            env_build_hash != image_hash,
        ])

    def save_environment_json(self):
        """Save on disk Python and build image versions used to create the venv."""
        data = {
            'python': {
                'version': self.config.python_full_version,
            },
        }

        if isinstance(self.build_env, DockerBuildEnvironment):
            build_image = self.config.build.image or DOCKER_IMAGE
            data.update({
                'build': {
                    'image': build_image,
                    'hash': self.build_env.image_hash,
                },
            })

        with open(self.environment_json_path(), 'w') as fpath:
            # Compatibility for Py2 and Py3. ``io.TextIOWrapper`` expects
            # unicode but ``json.dumps`` returns str in Py2.
            fpath.write(six.text_type(json.dumps(data)))


class Virtualenv(PythonEnvironment):

    """
    A virtualenv_ environment.

    .. _virtualenv: https://virtualenv.pypa.io/
    """

    def venv_path(self):
        return os.path.join(self.project.doc_path, 'envs', self.version.slug)

    def setup_base(self):
        site_packages = '--no-site-packages'
        if self.config.python.use_system_site_packages:
            site_packages = '--system-site-packages'
        env_path = self.venv_path()
        self.build_env.run(
            self.config.python_interpreter,
            '-mvirtualenv',
            site_packages,
            '--no-download',
            env_path,
            bin_path=None,  # Don't use virtualenv bin that doesn't exist yet
            cwd=self.checkout_path,
        )

    def install_core_requirements(self):
        """Install basic Read the Docs requirements into the virtualenv."""
        requirements = [
            'Pygments==2.2.0',
            # Assume semver for setuptools version, support up to next backwards
            # incompatible release
            self.project.get_feature_value(
                Feature.USE_SETUPTOOLS_LATEST,
                positive='setuptools<41',
                negative='setuptools<40',
            ),
            'docutils==0.13.1',
            'mock==1.0.1',
            'pillow==2.6.1',
            'alabaster>=0.7,<0.8,!=0.7.5',
            'commonmark==0.5.4',
            'recommonmark==0.4.0',
        ]

        if self.config.doctype == 'mkdocs':
            requirements.append('mkdocs==0.17.3')
        else:
            # We will assume semver here and only automate up to the next
            # backward incompatible release: 2.x
            requirements.extend([
                self.project.get_feature_value(
                    Feature.USE_SPHINX_LATEST,
                    positive='sphinx<2',
                    negative='sphinx<1.8',
                ),
                'sphinx-rtd-theme<0.5',
                'readthedocs-sphinx-ext<0.6'
            ])

        cmd = [
            'python',
            self.venv_bin(filename='pip'),
            'install',
            '--upgrade',
            '--cache-dir',
            self.project.pip_cache_path,
        ]
        if self.config.python.use_system_site_packages:
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            cmd.append('-I')
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path  # noqa - no comma here in py27 :/
        )

    def install_user_requirements(self):
        requirements_file_path = self.config.python.requirements
        if not requirements_file_path and requirements_file_path != '':
            builder_class = get_builder_class(self.config.doctype)
            docs_dir = (builder_class(build_env=self.build_env, python_env=self)
                        .docs_dir())
            paths = [docs_dir, '']
            req_files = ['pip_requirements.txt', 'requirements.txt']
            for path, req_file in itertools.product(paths, req_files):
                test_path = os.path.join(self.checkout_path, path, req_file)
                if os.path.exists(test_path):
                    requirements_file_path = test_path
                    break

        if requirements_file_path:
            args = [
                'python',
                self.venv_bin(filename='pip'),
                'install',
            ]
            if self.project.has_feature(Feature.PIP_ALWAYS_UPGRADE):
                args += ['--upgrade']
            args += [
                '--exists-action=w',
                '--cache-dir',
                self.project.pip_cache_path,
                '-r',
                requirements_file_path,
            ]
            self.build_env.run(
                *args,
                cwd=self.checkout_path,
                bin_path=self.venv_bin()  # noqa - no comma here in py27 :/
            )


class Conda(PythonEnvironment):

    """
    A Conda_ environment.

    .. _Conda: https://conda.io/docs/
    """

    def venv_path(self):
        return os.path.join(self.project.doc_path, 'conda', self.version.slug)

    def setup_base(self):
        conda_env_path = os.path.join(self.project.doc_path, 'conda')
        version_path = os.path.join(conda_env_path, self.version.slug)

        if os.path.exists(version_path):
            # Re-create conda directory each time to keep fresh state
            log.info(LOG_TEMPLATE.format(
                project=self.project.slug,
                version=self.version.slug,
                msg='Removing existing conda directory',
            ))
            shutil.rmtree(version_path)
        self.build_env.run(
            'conda',
            'env',
            'create',
            '--name',
            self.version.slug,
            '--file',
            self.config.conda.environment,
            bin_path=None,  # Don't use conda bin that doesn't exist yet
            cwd=self.checkout_path,
        )

    def install_core_requirements(self):
        """Install basic Read the Docs requirements into the Conda env."""
        # Use conda for requirements it packages
        requirements = [
            'mock',
            'pillow',
        ]

        # Install pip-only things.
        pip_requirements = [
            'recommonmark',
        ]

        if self.config.doctype == 'mkdocs':
            pip_requirements.append('mkdocs')
        else:
            pip_requirements.append('readthedocs-sphinx-ext')
            requirements.extend(['sphinx', 'sphinx_rtd_theme'])

        cmd = [
            'conda',
            'install',
            '--yes',
            '--name',
            self.version.slug,
        ]
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            cwd=self.checkout_path  # noqa - no comma here in py27 :/
        )

        pip_cmd = [
            'python',
            self.venv_bin(filename='pip'),
            'install',
            '-U',
            '--cache-dir',
            self.project.pip_cache_path,
        ]
        pip_cmd.extend(pip_requirements)
        self.build_env.run(
            *pip_cmd,
            bin_path=self.venv_bin(),
            cwd=self.checkout_path  # noqa - no comma here in py27 :/
        )

    def install_user_requirements(self):
        # as the conda environment was created by using the ``environment.yml``
        # defined by the user, there is nothing to update at this point
        pass
