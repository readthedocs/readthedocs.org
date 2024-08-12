"""Project app config."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "readthedocs.projects"

    def ready(self):
        # Load and register notification messages for this application
        import readthedocs.projects.notifications  # noqa
        import readthedocs.projects.signals  # noqa
        import readthedocs.projects.tasks.builds  # noqa
        import readthedocs.projects.tasks.search  # noqa
        import readthedocs.projects.tasks.utils  # noqa
