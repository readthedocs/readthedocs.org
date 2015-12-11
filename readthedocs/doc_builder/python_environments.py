import logging
import os
import shutil

from django.conf import settings

from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.projects.constants import LOG_TEMPLATE

log = logging.getLogger(__name__)


class PythonEnvironment(object):

    def __init__(self, task):
        self.task = task
        self.checkout_path = self.task.project.checkout_path(self.task.version.slug)

    def _log(self, msg):
        log.info(LOG_TEMPLATE
                 .format(project=self.task.project.slug,
                         version=self.task.version.slug,
                         msg=msg))

    def delete_existing_build_dir(self):

        # Handle deleting old build dir
        build_dir = os.path.join(
            self.task.project.venv_path(version=self.task.version.slug),
            'build')
        if os.path.exists(build_dir):
            self._log('Removing existing build directory')
            shutil.rmtree(build_dir)

    def install_package(self, config):
        setup_path = os.path.join(self.checkout_path, 'setup.py')
        if os.path.isfile(setup_path) and self.task.project.install_project:
            if getattr(settings, 'USE_PIP_INSTALL', False):
                self.task.build_env.run(
                    'python',
                    self.task.project.venv_bin(version=self.task.version.slug, filename='pip'),
                    'install',
                    '--ignore-installed',
                    '--cache-dir',
                    self.task.project.pip_cache_path,
                    '.',
                    cwd=self.checkout_path,
                    bin_path=self.task.project.venv_bin(version=self.task.version.slug)
                )
            else:
                self.task.build_env.run(
                    'python',
                    'setup.py',
                    'install',
                    '--force',
                    cwd=self.checkout_path,
                    bin_path=self.task.project.venv_bin(version=self.task.version.slug)
                )


class Virtualenv(PythonEnvironment):

    def setup_base(self, config):
        site_packages = '--no-site-packages'
        if self.task.project.use_system_packages:
            site_packages = '--system-site-packages'
        env_path = self.task.project.venv_path(version=self.task.version.slug)
        self.task.build_env.run(
            self.task.project.python_interpreter,
            '-mvirtualenv',
            site_packages,
            env_path,
        )

    def install_core_requirements(self, config):
        requirements = [
            'sphinx==1.3.1',
            'Pygments==2.0.2',
            'setuptools==18.6.1',
            'docutils==0.11',
            'mkdocs==0.14.0',
            'mock==1.0.1',
            'pillow==2.6.1',
            'readthedocs-sphinx-ext==0.5.4',
            'sphinx-rtd-theme==0.1.9',
            'alabaster>=0.7,<0.8,!=0.7.5',
            'recommonmark==0.1.1',
        ]

        cmd = [
            'python',
            self.task.project.venv_bin(version=self.task.version.slug, filename='pip'),
            'install',
            '--use-wheel',
            '-U',
            '--cache-dir',
            self.task.project.pip_cache_path,
        ]
        if self.task.project.use_system_packages:
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            cmd.append('-I')
        cmd.extend(requirements)
        self.task.build_env.run(
            *cmd,
            bin_path=self.task.project.venv_bin(version=self.task.version.slug)
        )

    def install_user_requirements(self, config):
        requirements_file_path = self.task.project.requirements_file
        if not requirements_file_path:
            builder_class = get_builder_class(self.task.project.documentation_type)
            docs_dir = (builder_class(self.task.build_env)
                        .docs_dir())
            for path in [docs_dir, '']:
                for req_file in ['pip_requirements.txt', 'requirements.txt']:
                    test_path = os.path.join(self.checkout_path, path, req_file)
                    if os.path.exists(test_path):
                        requirements_file_path = test_path
                        break

        if requirements_file_path:
            self.task.build_env.run(
                'python',
                self.task.project.venv_bin(version=self.task.version.slug, filename='pip'),
                'install',
                '--exists-action=w',
                '--cache-dir',
                self.task.project.pip_cache_path,
                '-r{0}'.format(requirements_file_path),
                cwd=self.checkout_path,
                bin_path=self.task.project.venv_bin(version=self.task.version.slug)
            )


class Conda(PythonEnvironment):

    def setup_base(self, config):
        env_path = self.task.project.venv_path(version=self.task.version.slug)
        if 'python' in config:
            python_version = config['python'].get('version', 2)
        else:
            python_version = 2
        if not os.path.exists(env_path):
            self.task.build_env.run(
                'conda',
                'create',
                '--yes',
                '--prefix',
                env_path,
                'python={python_version}'.format(python_version=python_version),
            )

    def install_core_requirements(self, config):
        requirements = [
            'sphinx==1.3.1',
            'Pygments==2.0.2',
            'docutils==0.11',
            # 'mkdocs==0.14.0',
            'mock==1.0.1',
            'pillow==3.0.0',
            # 'readthedocs-sphinx-ext==0.5.4',
            'sphinx_rtd_theme==0.1.7',
            'alabaster>=0.7,<0.8,!=0.7.5',
            # 'recommonmark==0.1.1',
        ]

        cmd = [
            'conda',
            'install',
            '-y',
        ]
        cmd.extend(requirements)
        self.task.build_env.run(
            *cmd,
            bin_path=self.task.project.venv_bin(version=self.task.version.slug)
        )

    def install_user_requirements(self, config):
        conda_env_path = os.path.join(self.task.project.doc_path, 'conda')
        self.task.build_env.run(
            'conda',
            'env',
            'update',
            '--name',
            self.task.version.slug,
            '--file',
            config['conda']['file'],
            cwd=self.checkout_path,
            environment={'CONDA_ENVS_PATH': conda_env_path}
        )
