"""Tasks for OAuth services"""

from __future__ import absolute_import
from django.contrib.auth.models import User

from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import permission_check
from readthedocs.core.utils.tasks import user_id_matches
from .services import registry


@permission_check(user_id_matches)
class SyncRemoteRepositories(PublicTask):

    name = __name__ + '.sync_remote_repositories'
    public_name = 'sync_remote_repositories'
    queue = 'web'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        for service_cls in registry:
            for service in service_cls.for_user(user):
                # TODO: handle the serialization of a simple ``Exception``
                # raised inside the task. Celery is returning:
                # EncodeError('Object of type Exception is not JSON
                # serializable'). Because of this, the task never ends and the
                # FE keeps waiting forever. Also, if we have 3 accounts
                # connected and the first one fails, the other two are not
                # executed.
                try:
                    service.sync()
                except Exception:
                    pass


sync_remote_repositories = SyncRemoteRepositories()
