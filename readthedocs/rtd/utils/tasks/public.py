from celery import Task


__all__ = ('PublicTask')


class PublicTask(Task):
    public_name = 'unknown'

    @classmethod
    def check_permission(cls, request, state, context):
        """
        Override this method to define who can monitor this task.
        """
        return False

    def get_task_data(self):
        """
        Return a tuple with the state that should be set next and the results
        task.
        """
        state = 'STARTED'
        info = {
            'task_name': self.name,
            'context': self.request.get('permission_context', {}),
            'public_data': self.request.get('public_data', {}),
        }
        return state, info

    def update_progress_data(self):
        state, info = self.get_task_data()
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
        state, info = self.get_task_data()
        return info

    def run_public(self, *args, **kwargs):
        raise NotImplementedError(
            'Public tasks must define the run_public method.')
