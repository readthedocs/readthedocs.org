"""Project signals."""

from dataclasses import asdict

import django.dispatch
import structlog
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.core.unresolver import get_project_cache_key
from readthedocs.integrations.models import GitHubAppIntegrationProviderData
from readthedocs.integrations.models import Integration
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


before_vcs = django.dispatch.Signal()

before_build = django.dispatch.Signal()

# Used to purge files from the CDN
files_changed = django.dispatch.Signal()


@receiver(post_save, sender=Project)
def create_integration_on_github_app_project(instance, *args, **kwargs):
    """Create a GitHub App integration when a project is linked to a GitHub App."""
    project = instance
    if not project.is_github_app_project:
        return

    integration, _ = project.integrations.get_or_create(
        integration_type=Integration.GITHUBAPP,
    )
    # Save some metadata about the GitHub App installation and repository,
    # so we can know which repository the project was linked to.
    remote_repo = project.remote_repository
    installation = project.remote_repository.github_app_installation
    integration.provider_data = asdict(
        GitHubAppIntegrationProviderData(
            installation_id=installation.installation_id,
            repository_id=int(remote_repo.remote_id),
            repository_full_name=remote_repo.full_name,
        )
    )
    integration.save()


@receiver(post_save, sender=Project)
@receiver(post_delete, sender=Project)
def invalidate_unresolver_project_cache(instance, *args, **kwargs):
    """
    Delete the project cached by the unresolver.

    We delete it right away and again after the transaction commits,
    otherwise a request served between the two would cache the old row again.
    """
    cache_key = get_project_cache_key(instance.slug)
    cache.delete(cache_key)
    transaction.on_commit(lambda: cache.delete(cache_key))
