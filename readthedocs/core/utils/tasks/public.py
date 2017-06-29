"""Celery tasks with publicly viewable status"""

from __future__ import absolute_import
from celery import Task, states
from django.conf import settings

from .retrieve import TaskNotFound
from .retrieve import get_task_data


__all__ = (
    'PublicTask', 'TaskNoPermission', 'permission_check',
    'get_public_task_data')


STATUS_UPDATES_ENABLED = not getattr(settings, 'CELERY_ALWAYS_EAGER', False)


class PublicTask(Task):

    """
    See oauth.tasks for usage example.

    Subclasses need to define a ``run_public`` method.
    """

    public_name = 'unknown'

    @classmethod
    def check_permission(cls, request, state, context):
        """Override this method to define who can monitor this task."""
        # pylint: disable=unused-argument
        return False

    def get_task_data(self):
        """Return tuple with state to be set next and results task."""
        state = 'STARTED'
        info = {
            'task_name': self.name,
            'context': self.request.get('permission_context', {}),
            'public_data': self.request.get('public_data', {}),
        }
        return state, info

    def update_progress_data(self):
        state, info = self.get_task_data()
        if STATUS_UPDATES_ENABLED:
            self.update_state(state=state, meta=info)

    def set_permission_context(self, context):
        """
        Set data that can be used by ``check_permission`` to authorize a

        request for the this task. By default it will be the ``kwargs`` passed
        into the task.
        """
        self.request.update(permission_context=context)
        self.update_progress_data()

    def set_public_data(self, data):
        """
        Set data that can be displayed in the frontend to authorized users.

        This might include progress data about the task.
        """
        self.request.update(public_data=data)
        self.update_progress_data()

    def run(self, *args, **kwargs):
        self.set_permission_context(kwargs)
        result = self.run_public(*args, **kwargs)
        if result is not None:
            self.set_public_data(result)
        _, info = self.get_task_data()
        return info

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Add the error to the task data"""
        _, info = self.get_task_data()
        if status == states.FAILURE:
            info['error'] = retval
        if STATUS_UPDATES_ENABLED:
            self.update_state(state=status, meta=info)


def permission_check(check):
    """
    Class decorator for subclasses of PublicTask to sprinkle in re-usable

    permission checks::

        @permission_check(user_id_matches)
        class MyTask(PublicTask):
            def run_public(self, user_id):
                pass
    """
    def decorator(cls):
        cls.check_permission = staticmethod(check)
        return cls
    return decorator


class TaskNoPermission(Exception):
    def __init__(self, task_id, *args, **kwargs):
        message = 'No permission to access task with id {id}'.format(
            id=task_id)
        super(TaskNoPermission, self).__init__(message, *args, **kwargs)


def get_public_task_data(request, task_id):
    """
    Return task details as tuple

    Will raise `TaskNoPermission` if `request` has no permission to access info
    of the task with id `task_id`. This is also the case of no task with the
    given id exists.

    :returns: (task name, task state, public data, error message)
    :rtype: (str, str, dict, str)
    """
    try:
        task, state, info = get_task_data(task_id)
    except TaskNotFound:
        # No task info has been found act like we don't have permission to see
        # the results.
        raise TaskNoPermission(task_id)

    if not hasattr(task, 'check_permission'):
        raise TaskNoPermission(task_id)

    context = info.get('context', {})
    if not task.check_permission(request, state, context):
        raise TaskNoPermission(task_id)
    public_name = task.public_name
    return public_name, state, info.get('public_data', {}), info.get('error', None)
