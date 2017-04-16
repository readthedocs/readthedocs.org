import logging
import os
import shutil

from django.conf import settings

from readthedocs.doc_builder.config import ConfigWrapper
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.projects.constants import LOG_TEMPLATE

log = logging.getLogger(__name__)


class PythonEnvironment(object):

    def __init__(self, version, build_env, config=None):
        self.version = version
        self.project = version.project
        self.build_env = build_env
        if config:
            self.config = config
        else:
            self.config = ConfigWrapper(version=version, yaml_config={})
        # Compute here, since it's used a lot
        self.checkout_path = self.project.checkout_path(self.version.slug)

    def _log(self, msg):
        log.info(LOG_TEMPLATE
                 .format(project=self.project.slug,
                         version=self.version.slug,
                         msg=msg))

    def delete_existing_build_dir(self):

        # Handle deleting old build dir
        build_dir = os.path.join(
            self.venv_path(),
            'build')
        if os.path.exists(build_dir):
            self._log('Removing existing build directory')
            shutil.rmtree(build_dir)

    def install_package(self):
        setup_path = os.path.join(self.checkout_path, 'setup.py')
        if os.path.isfile(setup_path) and self.config.install_project:
            if self.config.pip_install or getattr(settings, 'USE_PIP_INSTALL', False):
                extra_req_param = ''
                if self.config.extra_requirements:
                    extra_req_param = '[{0}]'.format(
                        ','.join(self.config.extra_requirements))
                self.build_env.run(
                    'python',
                    self.venv_bin(filename='pip'),
                    'install',
                    '--ignore-installed',
                    '--cache-dir',
                    self.project.pip_cache_path,
                    '.{0}'.format(extra_req_param),
                    cwd=self.checkout_path,
                    bin_path=self.venv_bin()
                )
            else:
                self.build_env.run(
                    'python',
                    'setup.py',
                    'install',
                    '--force',
                    cwd=self.checkout_path,
                    bin_path=self.venv_bin()
                )

    def venv_bin(self, filename=None):
        """Return path to the virtualenv bin path, or a specific binary

        :param filename: If specified, add this filename to the path return
        :returns: Path to virtualenv bin or filename in virtualenv bin
        """
        parts = [self.venv_path(), 'bin']
        if filename is not None:
            parts.append(filename)
        return os.path.join(*parts)


class Virtualenv(PythonEnvironment):

    def venv_path(self):
        return os.path.join(self.project.doc_path, 'envs', self.version.slug)

    def setup_base(self):
        site_packages = '--no-site-packages'
        if self.config.use_system_site_packages:
            site_packages = '--system-site-packages'
        env_path = self.venv_path()
        self.build_env.run(
            self.config.python_interpreter,
            '-mvirtualenv',
            site_packages,
            '--no-download',
            env_path,
            bin_path=None,  # Don't use virtualenv bin that doesn't exist yet
        )

    def install_core_requirements(self):
        requirements = [
            'sphinx==1.5.3',
            'Pygments==2.1.3',
            'setuptools==28.8.0',
            'docutils==0.13.1',
            'mkdocs==0.15.0',
            'mock==1.0.1',
            'pillow==2.6.1',
            ('git+https://github.com/rtfd/readthedocs-sphinx-ext.git'
             '@0.6-alpha#egg=readthedocs-sphinx-ext'),
            'sphinx-rtd-theme<0.3',
            'alabaster>=0.7,<0.8,!=0.7.5',
            'commonmark==0.5.4',
            'recommonmark==0.4.0',
        ]

        cmd = [
            'python',
            self.venv_bin(filename='pip'),
            'install',
            '--use-wheel',
            '-U',
            '--cache-dir',
            self.project.pip_cache_path,
        ]
        if self.config.use_system_site_packages:
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            cmd.append('-I')
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin()
        )

    def install_user_requirements(self):
        requirements_file_path = self.config.requirements_file
        if not requirements_file_path:
            builder_class = get_builder_class(self.project.documentation_type)
            docs_dir = (builder_class(build_env=self.build_env, python_env=self)
                        .docs_dir())
            for path in [docs_dir, '']:
                for req_file in ['pip_requirements.txt', 'requirements.txt']:
                    test_path = os.path.join(self.checkout_path, path, req_file)
                    if os.path.exists(test_path):
                        requirements_file_path = test_path
                        break

        if requirements_file_path:
            self.build_env.run(
                'python',
                self.venv_bin(filename='pip'),
                'install',
                '--exists-action=w',
                '--cache-dir',
                self.project.pip_cache_path,
                '-r{0}'.format(requirements_file_path),
                cwd=self.checkout_path,
                bin_path=self.venv_bin()
            )


class Conda(PythonEnvironment):

    def venv_path(self):
        return os.path.join(self.project.doc_path, 'conda', self.version.slug)

    def setup_base(self):
        conda_env_path = os.path.join(self.project.doc_path, 'conda')
        version_path = os.path.join(conda_env_path, self.version.slug)

        if os.path.exists(version_path):
            # Re-create conda directory each time to keep fresh state
            self._log('Removing existing conda directory')
            shutil.rmtree(version_path)
        self.build_env.run(
            'conda',
            'env',
            'create',
            '--name',
            self.version.slug,
            '--file',
            self.config.conda_file,
            bin_path=None,  # Don't use conda bin that doesn't exist yet
        )

    def install_core_requirements(self):

        # Use conda for requirements it packages
        requirements = [
            'sphinx==1.3.5',
            'Pygments==2.1.1',
            'docutils==0.12',
            'mock',
            'pillow==3.0.0',
            'sphinx_rtd_theme==0.1.7',
            'alabaster>=0.7,<0.8,!=0.7.5',
        ]

        cmd = [
            'conda',
            'install',
            '--yes',
            '--name',
            self.version.slug,
        ]
        cmd.extend(requirements)
        self.build_env.run(
            *cmd
        )

        # Install pip-only things.
        pip_requirements = [
            'mkdocs==0.15.0',
            ('git+https://github.com/rtfd/readthedocs-sphinx-ext.git'
             '@0.6-alpha#egg=readthedocs-sphinx-ext'),
            'commonmark==0.5.4',
            'recommonmark==0.1.1',
        ]

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
            bin_path=self.venv_bin()
        )

    def install_user_requirements(self):
        self.build_env.run(
            'conda',
            'env',
            'update',
            '--name',
            self.version.slug,
            '--file',
            self.config.conda_file,
        )
