"""Endpoints relating to task/job status, etc."""

import structlog
from django.core.cache import cache
from django.urls import reverse
from rest_framework import decorators
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from readthedocs.oauth import tasks


log = structlog.get_logger(__name__)


@decorators.api_view(["GET"])
@decorators.permission_classes((permissions.AllowAny,))
@decorators.renderer_classes((JSONRenderer,))
def job_status(request, task_id):
    """Retrieve Celery task function state from frontend."""
    # HACK: always poll up to N times and after that return the sync has
    # finished. This is a way to avoid re-enabling Celery result backend for now.
    # TODO remove this API and RemoteRepo sync UI when we have better auto syncing
    poll_n = cache.get(task_id, 0)
    poll_n += 1
    cache.set(task_id, poll_n, 5 * 60)
    finished = poll_n == 5

    data = {
        "name": "sync_remote_repositories",
        "data": {},
        "started": True,
        "finished": finished,
        "success": finished,
    }
    return Response(data)


@decorators.api_view(["POST"])
@decorators.permission_classes((permissions.IsAuthenticated,))
@decorators.renderer_classes((JSONRenderer,))
def sync_remote_repositories(request):
    """Trigger a re-sync of remote repositories for the user."""
    result = tasks.sync_remote_repositories.delay(
        user_id=request.user.id,
    )
    task_id = result.task_id
    return Response(
        {
            "task_id": task_id,
            "url": reverse("api_job_status", kwargs={"task_id": task_id}),
        }
    )
