class ConfigWrapper(object):

    """
    A config object that wraps the Project & YAML based configs.

    Gives precidence to YAML, falling back to project if it isn't defined.
    """

    def __init__(self, project, yaml_config):
        self._project = project
        self._yaml_config = yaml_config

    @property
    def install_project(self):
        if 'install_project' in self._yaml_config:
            return self._yaml_config['install_project']
        else:
            return self._project.install_project

    @property
    def python_version(self):
        if 'version' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['version']
        else:
            return self._project.python_interpreter

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
