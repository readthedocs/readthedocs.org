from django.contrib.auth.models import User
from djcelery import celery as celery_app

from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import permission_check
from readthedocs.core.utils.tasks import user_id_matches
from .utils import import_bitbucket
from .utils import import_github


@permission_check(user_id_matches)
class SyncGitHubRepositories(PublicTask):
    public_name = 'sync_github_repositories'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        import_github(user, sync=True)


sync_github_repositories = celery_app.tasks[SyncGitHubRepositories.name]


@permission_check(user_id_matches)
class SyncBitBucketRepositories(PublicTask):
    public_name = 'sync_bitbucket_repositories'

    def run_public(self, user_id):
        user = User.objects.get(pk=user_id)
        import_bitbucket(user, sync=True)


sync_bitbucket_repositories = celery_app.tasks[SyncBitBucketRepositories.name]
