import logging

from rest_framework import decorators, permissions
from rest_framework.renderers import JSONPRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response

from rtd.utils.tasks import TaskNoPermission
from rtd.utils.tasks import get_public_task_data


log = logging.getLogger(__name__)


SUCCESS_STATES = ('SUCCESS',)
FAILURE_STATES = ('FAILURE', 'REVOKED',)
FINISHED_STATES = SUCCESS_STATES + FAILURE_STATES
STARTED_STATES = ('RECEIVED', 'STARTED', 'RETRY') + FINISHED_STATES


def get_status_data(task_name, state, data):
    return {
        'name': task_name,
        'data': data,
        'started': state in STARTED_STATES,
        'finished': state in FINISHED_STATES,
        'success': state in SUCCESS_STATES,
    }


@decorators.api_view(['GET'])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes(
    (JSONRenderer, JSONPRenderer, BrowsableAPIRenderer))
def job_status(request, task_id):
    try:
        task_name, state, public_data = get_public_task_data(request, task_id)
    except TaskNoPermission:
        return Response(
            get_status_data('unknown', 'PENDING', {}))
    return Response(
        get_status_data(task_name, state, public_data))
