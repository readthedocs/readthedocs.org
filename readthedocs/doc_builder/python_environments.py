import logging
import os
import shutil

from django.conf import settings

from readthedocs.builds.constants import LATEST
from readthedocs.doc_builder.loader import get_builder_class
from readthedocs.projects.constants import LOG_TEMPLATE

log = logging.getLogger(__name__)


class PythonEnvironment(object):

    def __init__(self, project, version, build_env):
        self.project = project
        self.version = version
        self.build_env = build_env
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
            self.venv_path(version=self.version.slug),
            'build')
        if os.path.exists(build_dir):
            self._log('Removing existing build directory')
            shutil.rmtree(build_dir)

    def install_package(self, config):
        setup_path = os.path.join(self.checkout_path, 'setup.py')
        if os.path.isfile(setup_path) and self.project.install_project:
            if getattr(settings, 'USE_PIP_INSTALL', False):
                self.build_env.run(
                    'python',
                    self.venv_bin(version=self.version.slug, filename='pip'),
                    'install',
                    '--ignore-installed',
                    '--cache-dir',
                    self.project.pip_cache_path,
                    '.',
                    cwd=self.checkout_path,
                    bin_path=self.venv_bin(version=self.version.slug)
                )
            else:
                self.build_env.run(
                    'python',
                    'setup.py',
                    'install',
                    '--force',
                    cwd=self.checkout_path,
                    bin_path=self.venv_bin(version=self.version.slug)
                )

    def venv_bin(self, version=LATEST, filename=None):
        """Return path to the virtualenv bin path, or a specific binary

        :param version: Version slug to use in path name
        :param filename: If specified, add this filename to the path return
        :returns: Path to virtualenv bin or filename in virtualenv bin
        """
        parts = [self.venv_path(version), 'bin']
        if filename is not None:
            parts.append(filename)
        return os.path.join(*parts)


class Virtualenv(PythonEnvironment):

    def venv_path(self, version=LATEST):
        return os.path.join(self.doc_path, 'envs', version)

    def setup_base(self, config):
        site_packages = '--no-site-packages'
        if self.project.use_system_packages:
            site_packages = '--system-site-packages'
        env_path = self.venv_path(version=self.version.slug)
        self.build_env.run(
            self.project.python_interpreter,
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
            self.venv_bin(version=self.version.slug, filename='pip'),
            'install',
            '--use-wheel',
            '-U',
            '--cache-dir',
            self.project.pip_cache_path,
        ]
        if self.project.use_system_packages:
            # Other code expects sphinx-build to be installed inside the
            # virtualenv.  Using the -I option makes sure it gets installed
            # even if it is already installed system-wide (and
            # --system-site-packages is used)
            cmd.append('-I')
        cmd.extend(requirements)
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(version=self.version.slug)
        )

    def install_user_requirements(self, config):
        requirements_file_path = self.project.requirements_file
        if not requirements_file_path:
            builder_class = get_builder_class(self.project.documentation_type)
            docs_dir = (builder_class(self.build_env)
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
                self.venv_bin(version=self.version.slug, filename='pip'),
                'install',
                '--exists-action=w',
                '--cache-dir',
                self.project.pip_cache_path,
                '-r{0}'.format(requirements_file_path),
                cwd=self.checkout_path,
                bin_path=self.venv_bin(version=self.version.slug)
            )


class Conda(PythonEnvironment):

    def venv_path(self, version=LATEST):
        return os.path.join(self.doc_path, 'conda', version)

    def setup_base(self, config):
        env_path = self.venv_path(version=self.version.slug)
        if 'python' in config:
            python_version = config['python'].get('version', 2)
        else:
            python_version = 2
        if not os.path.exists(env_path):
            self.build_env.run(
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
        self.build_env.run(
            *cmd,
            bin_path=self.venv_bin(version=self.version.slug)
        )

    def install_user_requirements(self, config):
        conda_env_path = os.path.join(self.project.doc_path, 'conda')
        self.build_env.run(
            'conda',
            'env',
            'update',
            '--name',
            self.version.slug,
            '--file',
            config['conda']['file'],
            cwd=self.checkout_path,
            environment={'CONDA_ENVS_PATH': conda_env_path}
        )
