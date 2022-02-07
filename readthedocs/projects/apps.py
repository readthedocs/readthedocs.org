"""Project app config."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):

    name = 'readthedocs.projects'

    def ready(self):
        # TODO: remove this import after the deploy together with the
        # `tasks/__init__.py` file
        import readthedocs.projects.tasks

        import readthedocs.projects.tasks.builds
        import readthedocs.projects.tasks.search
        import readthedocs.projects.tasks.utils
