import structlog
from allauth.account.signals import user_logged_in
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.tasks import sync_remote_repositories

log = structlog.get_logger(__name__)


@receiver(user_logged_in, sender=User)
def sync_remote_repositories_on_login(sender, request, user, *args, **kwargs):
    """
    Sync ``RemoteRepository`` objects when a user logs in via Social Login.

    This function will trigger a background task that will pull down
    repositories from all the user's Social Account connected and create/update
    their ``RemoteRepository`` in our database.
    """
    log.info(
        "Triggering sync RemoteRepository in background on login.",
        user_username=user.username,
    )
    sync_remote_repositories.delay(user.pk)


@receiver(post_save, sender=RemoteRepository)
def update_project_clone_url(sender, instance, created, *args, **kwargs):
    """Update the clone URL for all projects linked to this RemoteRepository."""
    instance.projects.all().update(repo=instance.clone_url)
