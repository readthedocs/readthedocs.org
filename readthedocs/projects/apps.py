"""Project app config."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "readthedocs.projects"

    def ready(self):
        import readthedocs.projects.tasks.builds  # noqa
        import readthedocs.projects.tasks.search  # noqa
        import readthedocs.projects.tasks.utils  # noqa
