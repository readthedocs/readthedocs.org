"""Project signals."""

from dataclasses import asdict

import django.dispatch
import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

from readthedocs.integrations.models import GitHubAppIntegrationProviderData
from readthedocs.integrations.models import Integration
from readthedocs.projects.models import AddonsConfig
from readthedocs.projects.models import Group
from readthedocs.projects.models import Project
from readthedocs.projects.models import ProjectRelationship


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


@receiver(post_save, sender=ProjectRelationship)
def add_subprojects_to_group(sender, instance, created, **kwargs):
    """
    Automatically add subprojects to the parent project's subproject group.

    When a subproject relationship is created, add the child to a group
    named after the parent project with "_subprojects" suffix.
    """
    if created:
        parent = instance.parent
        child = instance.child
        group_name = f"{parent.name} - Subprojects"
        group_slug = f"{parent.slug}-subprojects"

        # Get or create the group for subprojects
        group, _ = Group.objects.get_or_create(
            slug=group_slug,
            defaults={"name": group_name},
        )

        # Add both parent and child to the group
        group.projects.add(parent, child)
        log.info(
            "Added subproject to group",
            parent_slug=parent.slug,
            child_slug=child.slug,
            group_slug=group_slug,
        )


@receiver(post_save, sender=Project)
def add_translations_to_group(sender, instance, created, **kwargs):
    """
    Automatically add translations to the main language project's translation group.

    When a project has a main_language_project, add it to a group
    named after the main language project with "_translations" suffix.
    """
    project = instance
    if project.main_language_project:
        main_project = project.main_language_project
        group_name = f"{main_project.name} - Translations"
        group_slug = f"{main_project.slug}-translations"

        # Get or create the group for translations
        group, _ = Group.objects.get_or_create(
            slug=group_slug,
            defaults={"name": group_name},
        )

        # Add both main project and translation to the group
        group.projects.add(main_project, project)
        log.info(
            "Added translation to group",
            main_project_slug=main_project.slug,
            translation_slug=project.slug,
            group_slug=group_slug,
        )
