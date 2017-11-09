"""Project app config"""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = 'readthedocs.projects'

    def ready(self):
        from readthedocs.projects.tasks import UpdateDocsTask
        from readthedocs.worker import app
        app.tasks.register(UpdateDocsTask)
