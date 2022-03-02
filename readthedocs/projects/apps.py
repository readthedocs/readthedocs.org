"""Project app config."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):

    name = 'readthedocs.projects'

    def ready(self):
        import readthedocs.projects.tasks.builds
        import readthedocs.projects.tasks.search
        import readthedocs.projects.tasks.utils
