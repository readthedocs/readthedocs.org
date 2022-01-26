# -*- coding: utf-8 -*-

"""Project app config."""

from django.apps import AppConfig

from readthedocs.worker import app, register_renamed_tasks


class ProjectsConfig(AppConfig):

    name = 'readthedocs.projects'

    def ready(self):
        import readthedocs.projects.tasks.builds
        import readthedocs.projects.tasks.search
        import readthedocs.projects.tasks.utils

        # TODO: remove calling to `register_renamed_tasks` after deploy
        renamed_tasks = {
            'readthedocs.projects.tasks.update_docs_task': 'readthedocs.projects.tasks.builds.update_docs_task',
            'readthedocs.projects.tasks.sync_repository_task': 'readthedocs.projects.tasks.builds.sync_repository_task'
        }
        register_renamed_tasks(app, renamed_tasks)
