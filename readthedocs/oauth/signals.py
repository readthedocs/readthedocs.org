import structlog
from allauth.account.signals import user_logged_in
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.notifications.models import Notification
from readthedocs.oauth.migrate import has_projects_pending_migration
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.notifications import MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP
from readthedocs.oauth.tasks import sync_remote_repositories
from readthedocs.projects.models import Feature


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


@receiver(social_account_added, sender=SocialLogin)
def sync_remote_repositories_on_social_account_added(sender, request, sociallogin, *args, **kwargs):
    """Sync remote repositories when a new social account is added."""
    log.info(
        "Triggering remote repositories sync in background on social account added.",
        user_username=sociallogin.user.username,
    )
    sync_remote_repositories.delay(sociallogin.user.pk)


@receiver(post_save, sender=RemoteRepository)
def update_project_clone_url(sender, instance, created, *args, **kwargs):
    """Update the clone URL for all projects linked to this RemoteRepository."""
    instance.projects.exclude(feature__feature_id=Feature.DONT_SYNC_WITH_REMOTE_REPO).update(
        repo=instance.clone_url
    )


@receiver(social_account_added, sender=SocialLogin)
def notify_user_about_migration_on_github_app_connection(sender, request, sociallogin, **kwargs):
    provider = sociallogin.account.get_provider()
    if provider.id != GitHubAppProvider.id:
        return

    if has_projects_pending_migration(sociallogin.user):
        Notification.objects.add(
            message_id=MESSAGE_PROJECTS_TO_MIGRATE_TO_GITHUB_APP,
            attached_to=sociallogin.user,
            dismissable=True,
        )
