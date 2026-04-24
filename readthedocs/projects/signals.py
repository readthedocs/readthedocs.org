"""Project signals."""

from dataclasses import asdict

import django.dispatch
import structlog
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from readthedocs.audit.models import AuditLog
from readthedocs.core.history import get_audit_context
from readthedocs.integrations.models import GitHubAppIntegrationProviderData
from readthedocs.integrations.models import Integration
from readthedocs.projects.models import AddonsConfig
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


before_vcs = django.dispatch.Signal()

before_build = django.dispatch.Signal()
after_build = django.dispatch.Signal()

project_import = django.dispatch.Signal()

# Used to purge files from the CDN
files_changed = django.dispatch.Signal()


@receiver(post_save, sender=Project)
def create_addons_on_new_projects(instance, *args, **kwargs):
    """Create ``AddonsConfig`` on new projects."""
    AddonsConfig.objects.get_or_create(project=instance)


@receiver(pre_delete, sender=Project)
def audit_project_deletion(sender, instance, **kwargs):
    """
    Log the deletion in each project admin's security log.

    Fires for both direct deletions and cascade deletions (e.g. when an
    organization is deleted). If no acting user is set on the context (e.g.
    tests or management commands that bypass ``delete_object``), we skip the
    audit log entirely — there's no one to attribute the deletion to.
    """
    acting_user, ip, browser = get_audit_context()
    if not acting_user:
        return
    data = {"deleted_by": acting_user.username}
    for admin in instance.users.all():
        AuditLog.objects.create(
            user=admin,
            action=AuditLog.PROJECT_DELETE,
            project=instance,
            ip=ip,
            browser=browser,
            data=data,
        )


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
