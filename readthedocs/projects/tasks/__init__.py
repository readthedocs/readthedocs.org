from readthedocs.worker import app

from .builds import update_docs_task as update_docs_task_new
from .builds import sync_repository_task as sync_repository_task_new
from .search import fileify as fileify_new
from .search import remove_search_indexes as remove_search_indexes_new
from .utils import remove_build_storage_paths as remove_build_storage_paths_new
from .utils import finish_inactive_builds as finish_inactive_builds_new


# TODO: remove this file completely after deploy.
#
# This file re-defines all the tasks that were moved from
# `readthedocs/projects/task.py` file into
# `readthedocs/projects/tasks/builds.py,search.py,utils.py` to keep the same
# names and be able to attend tasks triggered with the old names by old web
# instances during the deploy.
#
# Besides, if the signature of the task has changed, it alter the way the task
# is called passing the correct arguments

@app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=7 * 60,
)
def update_docs_task(self, version_pk, *args, **kwargs):
    update_docs_task_new.delay(
        version_pk,
        kwargs.get('build_pk'),
        build_commit=kwargs.get('commit'),
    )


@app.task(
    max_retries=5,
    default_retry_delay=7 * 60,
)
def sync_repository_task(version_pk):
    sync_repository_task_new.delay(version_pk)


@app.task(queue='reindex')
def fileify(version_pk, commit, build, search_ranking, search_ignore):
    fileify_new.delay(version_pk, commit, build, search_ranking, search_ignore)


@app.task(queue='web')
def remove_build_storage_paths(paths):
    remove_build_storage_paths_new.delay(paths)


@app.task(queue='web')
def remove_search_indexes(project_slug, version_slug=None):
    remove_search_indexes_new.delay(project_slug, version_slug=version_slug)


@app.task()
def finish_inactive_builds():
    finish_inactive_builds_new.delay()
