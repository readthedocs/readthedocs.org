"""Project app config"""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = 'readthedocs.projects'

    def ready(self):
        from readthedocs.projects import tasks
        from readthedocs.worker import app
        app.tasks.register(tasks.SyncRepositoryTask)
        app.tasks.register(tasks.UpdateDocsTask)
