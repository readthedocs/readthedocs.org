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
            'readthedocs.projects.tasks.finish_inactive_builds': 'readthedocs.projects.tasks.utils.finish_inactive_builds',          # noqa
            'readthedocs.projects.tasks.update_docs_task': 'readthedocs.projects.tasks.builds.update_docs_task',                     # noqa
            'readthedocs.projects.tasks.fileify': 'readthedocs.projects.tasks.search.fileify',                                       # noqa
            'readthedocs.projects.tasks.remove_build_storage_paths': 'readthedocs.projects.tasks.utils.remove_build_storage_paths',  # noqa
            'readthedocs.projects.tasks.remove_search_indexes': 'readthedocs.projects.tasks.search.remove_search_indexes',           # noqa
            'readthedocs.projects.tasks.sync_repository_task': 'readthedocs.projects.tasks.builds.sync_repository_task'              # noqa
        }
        register_renamed_tasks(app, renamed_tasks)
