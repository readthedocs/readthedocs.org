# -*- coding: utf-8 -*-

"""Project app config."""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):

    name = 'readthedocs.projects'

    def ready(self):
        # import readthedocs.projects.tasks
        import readthedocs.projects.tasks.builds
        import readthedocs.projects.tasks.search
