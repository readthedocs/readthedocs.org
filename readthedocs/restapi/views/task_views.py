"""Endpoints relating to task/job status, etc."""

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

from django.core.urlresolvers import reverse
from redis import ConnectionError
from rest_framework import decorators, permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.core.utils.tasks import TaskNoPermission, get_public_task_data
from readthedocs.oauth import tasks

log = logging.getLogger(__name__)


SUCCESS_STATES = ('SUCCESS',)
FAILURE_STATES = ('FAILURE', 'REVOKED',)
FINISHED_STATES = SUCCESS_STATES + FAILURE_STATES
STARTED_STATES = ('RECEIVED', 'STARTED', 'RETRY') + FINISHED_STATES


def get_status_data(task_name, state, data, error=None):
    data = {
        'name': task_name,
        'data': data,
        'started': state in STARTED_STATES,
        'finished': state in FINISHED_STATES,
        # When an exception is raised inside the task, we keep this as SUCCESS
        # and add the exception message into the 'error' key
        'success': state in SUCCESS_STATES and error is None,
    }
    if error is not None:
        data['error'] = error
    return data


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def job_status(request, task_id):
    try:
        task_name, state, public_data, error = get_public_task_data(
            request, task_id
        )
    except (TaskNoPermission, ConnectionError):
        return Response(
            get_status_data('unknown', 'PENDING', {})
        )
    return Response(
        get_status_data(task_name, state, public_data, error)
    )


@decorators.api_view(['POST'])
@decorators.permission_classes((permissions.IsAuthenticated,))
@decorators.renderer_classes((JSONRenderer,))
def sync_remote_repositories(request):
    result = tasks.sync_remote_repositories.delay(
        user_id=request.user.id
    )
    task_id = result.task_id
    return Response({
        'task_id': task_id,
        'url': reverse('api_job_status', kwargs={'task_id': task_id}),
    })
