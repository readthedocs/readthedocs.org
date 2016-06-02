from readthedocs_build.config import (ConfigError, BuildConfig, InvalidConfig,
                                      load as load_config)


from readthedocs.projects.exceptions import ProjectImportError


class ConfigWrapper(object):

    """
    A config object that wraps the Project & YAML based configs.

    Gives precedence to YAML, falling back to project if it isn't defined.

    We only currently implement a subset of the existing YAML config.
    This should be the canonical source for our usage of the YAML files,
    never accessing the config object directly.

    """

    def __init__(self, version, yaml_config):
        self._version = version
        self._project = version.project
        self._yaml_config = yaml_config

    @property
    def pip_install(self):
        if 'pip_install' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['pip_install']
        else:
            return False

    @property
    def install_project(self):
        if self.pip_install:
            return True
        if 'setup_py_install' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['setup_py_install']
        else:
            return self._project.install_project

    @property
    def python_interpreter(self):
        if 'version' in self._yaml_config.get('python', {}):
            ver = self._yaml_config['python']['version']
            if str(ver).startswith('2'):
                return 'python'
            else:
                return 'python3'
        else:
            return self._project.python_interpreter

    @property
    def python_version(self):
        if 'version' in self._yaml_config.get('python', {}):
            ver = self._yaml_config['python']['version']
            return ver
        else:
            if self._project.python_interpreter == 'python':
                return 2
            else:
                return 3

    @property
    def use_system_site_packages(self):
        if 'use_system_site_packages' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['use_system_site_packages']
        else:
            return self._project.use_system_packages

    @property
    def use_conda(self):
        if 'conda' in self._yaml_config:
            return True
        else:
            return False

    @property
    def conda_file(self):
        if 'file' in self._yaml_config.get('conda', {}):
            return self._yaml_config['conda']['file']
        else:
            return None

    @property
    def requirements_file(self):
        if 'requirements_file' in self._yaml_config:
            return self._yaml_config['requirements_file']
        else:
            return self._project.requirements_file

    @property
    def formats(self):
        if 'formats' in self._yaml_config:
            return self._yaml_config['formats']
        else:
            formats = ['htmlzip']
            if self._project.enable_epub_build:
                formats += ['epub']
            if self._project.enable_pdf_build:
                formats += ['pdf']
            return formats

    # Not implemented until we figure out how to keep in sync with the webs.
    # Probably needs to be version-specific as well, not project.
    # @property
    # def documentation_type(self):
    #     if 'type' in self._yaml_config:
    #         return self._yaml_config['type']
    #     else:
    #         return self._project.documentation_type


def load_yaml_config(version):
    """
    Load a configuration from `readthedocs.yml` file.

    This uses the configuration logic from `readthedocs-build`,
    which will keep parsing consistent between projects.
    """

    checkout_path = version.project.checkout_path(version.slug)
    try:
        config = load_config(
            path=checkout_path,
            env_config={
                'output_base': '',
                'type': 'sphinx',
                'name': version.slug,
            },
        )[0]
    except InvalidConfig:  # This is a subclass of ConfigError, so has to come first
        raise
    except ConfigError:
        config = BuildConfig(
            env_config={},
            raw_config={},
            source_file='empty',
            source_position=0,
        )
    return ConfigWrapper(version=version, yaml_config=config)
