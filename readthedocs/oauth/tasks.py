"""Tasks for OAuth services"""

from __future__ import absolute_import
from celery import task
from django.contrib.auth.models import User
from djcelery import celery as celery_app

from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import permission_check
from readthedocs.core.utils.tasks import user_id_matches
from readthedocs.oauth.models import RemoteOrganization
from .services import registry


@permission_check(user_id_matches)
class SyncRemoteRepositories(PublicTask):
    public_name = 'sync_remote_repositories'
    queue = 'web'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        for service_cls in registry:
            for service in service_cls.for_user(user):
                service.sync()

@task()
def bulk_delete_oauth_remote_organizations(organizations_id):
    RemoteOrganization.objects.filter(id__in=organizations_id).delete()


sync_remote_repositories = celery_app.tasks[SyncRemoteRepositories.name]
