"""Utilities for retrieving task data."""

__all__ = ("TaskNotFound",)


class TaskNotFound(Exception):
    def __init__(self, task_id, *args, **kwargs):
        message = "No public task found with id {id}".format(id=task_id)
        super().__init__(message, *args, **kwargs)
