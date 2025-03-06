"""Celery tasks with publicly viewable status."""

from celery import Task
from celery import states
from django.conf import settings


__all__ = (
    "PublicTask",
    "TaskNoPermission",
)

STATUS_UPDATES_ENABLED = not settings.CELERY_ALWAYS_EAGER


# pylint: disable=abstract-method
# pylint: disable=broad-except
# pylint: disable=invalid-name
class PublicTask(Task):
    """
    Encapsulates common behaviour to expose a task publicly.

    Tasks should use this class as ``base``. And define a ``check_permission``
    property or use the ``permission_check`` decorator.

    The check_permission should be a function like:
    function(request, state, context), and needs to return a boolean value.

    See oauth.tasks for usage example.
    """

    def get_task_data(self):
        """Return tuple with state to be set next and results task."""
        state = states.STARTED
        info = {
            "task_name": self.name,
            "context": self.request.get("permission_context", {}),
            "public_data": self.request.get("public_data", {}),
        }
        return state, info

    def update_progress_data(self):
        state, info = self.get_task_data()
        if STATUS_UPDATES_ENABLED:
            self.update_state(state=state, meta=info)

    def set_permission_context(self, context):
        """
        Set data that can be used by ``check_permission`` to authorize a.

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

    def __call__(self, *args, **kwargs):
        # We override __call__ to let tasks use the run method.
        error = False
        exception_raised = None
        self.set_permission_context(kwargs)
        try:
            result = self.run(*args, **kwargs)
        except Exception as e:
            # With Celery 4 we lost the ability to keep our data dictionary into
            # ``AsyncResult.info`` when an exception was raised inside the
            # Task. In this case, ``info`` will contain the exception raised
            # instead of our data. So, I'm keeping the task as ``SUCCESS`` but
            # the adding the exception message into an ``error`` key to be used
            # from outside
            exception_raised = e
            error = True

        _, info = self.get_task_data()
        if error and exception_raised:
            info["error"] = str(exception_raised)
        elif result is not None:
            self.set_public_data(result)

        return info

    @staticmethod
    def permission_check(check):
        """
        Decorator for tasks that have PublicTask as base.

        .. note::

           The decorator should be on top of the task decorator.

        permission checks::

            @PublicTask.permission_check(user_id_matches)
            @celery.task(base=PublicTask)
            def my_public_task(user_id):
                pass
        """

        def decorator(func):
            func.check_permission = check
            return func

        return decorator


class TaskNoPermission(Exception):
    def __init__(self, task_id, *args, **kwargs):
        message = "No permission to access task with id {id}".format(
            id=task_id,
        )
        super().__init__(message, *args, **kwargs)
