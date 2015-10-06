from django.contrib.auth.models import User
from djcelery import celery as celery_app

from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import permission_check
from readthedocs.core.utils.tasks import user_id_matches
from .utils import import_bitbucket
from .utils import import_github


@permission_check(user_id_matches)
class SyncRemoteRepositories(PublicTask):
    public_name = 'sync_remote_repositories'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        import_github(user, sync=True)
        import_bitbucket(user, sync=True)


sync_remote_repositories = celery_app.tasks[SyncRemoteRepositories.name]
