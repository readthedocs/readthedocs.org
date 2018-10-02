"""Utilities for retrieving task data."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from celery import states
from celery.result import AsyncResult

__all__ = ('TaskNotFound', 'get_task_data')


class TaskNotFound(Exception):
    def __init__(self, task_id, *args, **kwargs):
        message = 'No public task found with id {id}'.format(id=task_id)
        super(TaskNotFound, self).__init__(message, *args, **kwargs)


def get_task_data(task_id):
    """
    Will raise `TaskNotFound` if the task is in state ``PENDING`` or the task

    meta data has no ``'task_name'`` key set.
    """
    from readthedocs.worker import app

    result = AsyncResult(task_id)
    state, info = result.state, result.info
    if state == states.PENDING:
        raise TaskNotFound(task_id)
    if 'task_name' not in info:
        raise TaskNotFound(task_id)
    try:
        task = app.tasks[info['task_name']]
    except KeyError:
        raise TaskNotFound(task_id)
    return task, state, info
