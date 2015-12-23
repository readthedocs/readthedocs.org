"""Tasks for OAuth services"""

from django.contrib.auth.models import User
from djcelery import celery as celery_app

from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import permission_check
from readthedocs.core.utils.tasks import user_id_matches
from .utils import services


@permission_check(user_id_matches)
class SyncRemoteRepositories(PublicTask):
    public_name = 'sync_remote_repositories'
    queue = 'web'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        for service_cls in services:
            service = service_cls.for_user(user)
            if service is not None:
                service.sync(sync=True)


sync_remote_repositories = celery_app.tasks[SyncRemoteRepositories.name]
