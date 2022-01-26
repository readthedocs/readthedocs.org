import structlog

from readthedocs.worker import app

from .builds import update_docs_task as update_docs_task_new
from .builds import sync_repository_task as sync_repository_task_new
from .search import fileify as fileify_new
from .search import remove_search_indexes as remove_search_indexes_new
from .utils import remove_build_storage_paths as remove_build_storage_paths_new
from .utils import finish_inactive_builds as finish_inactive_builds_new


log = structlog.get_logger(__name__)

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
    log.info(
        'Triggering the new `update_docs_task`',
        delivery_info=self.request.delivery_info,
    )

    update_docs_task_new.apply_async(
        args=[
            version_pk,
            kwargs.get('build_pk'),
        ],
        kwargs={
            'build_commit': kwargs.get('commit'),
        },
        queue=self.request.delivery_info.get('routing_key')
    )


@app.task(
    max_retries=5,
    default_retry_delay=7 * 60,
)
def sync_repository_task(version_pk):
    sync_repository_task_new.apply_async(
        args=[
            version_pk,
        ],
        kwargs={},
        queue=self.request.delivery_info.get('routing_key')
    )


@app.task(
    queue='reindex',
    bind=True,
)
def fileify(self, version_pk, commit, build, search_ranking, search_ignore):
    fileify_new.async_apply(
        args=[
            version_pk,
            commit,
            build,
            search_ranking,
            search_ignore,
        ],
        kwargs={},
        queue=self.request.delivery_info.get('routing_key')
    )


@app.task(
    queue='web',
    bind=True,
)
def remove_build_storage_paths(self, paths):
    remove_build_storage_paths_new.apply_async(
        args=[
            paths,
        ],
        kwargs={},
        queue=self.request.delivery_info.get('routing_key')
    )


@app.task(
    queue='web',
    bind=True,
)
def remove_search_indexes(self, project_slug, version_slug=None):
    remove_search_indexes_new.apply_async(
        args=[
            project_slug,
        ],
        kwargs={
            'version_slug': version_slug,
        },
        queue=self.request.delivery_info.get('routing_key')
    )


@app.task(
    bind=True,
)
def finish_inactive_builds(self):
    finish_inactive_builds_new.apply_async(
        args=[],
        kwargs={},
        queue=self.request.delivery_info.get('routing_key')
    )
