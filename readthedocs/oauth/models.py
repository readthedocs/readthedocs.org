"""OAuth service models."""

from functools import cached_property

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from readthedocs.projects.constants import REPO_CHOICES
from readthedocs.projects.models import Project

from .constants import GITHUB_APP
from .constants import VCS_PROVIDER_CHOICES
from .querysets import RemoteOrganizationQuerySet
from .querysets import RemoteRepositoryQuerySet


log = structlog.get_logger(__name__)


class GitHubAppInstallationManager(models.Manager):
    def get_or_create_installation(
        self, *, installation_id, target_id, target_type, extra_data=None
    ):
        """
        Get or create a GitHub app installation.

        Only the installation_id is unique, the target_id and target_type could change,
        but this should never happen.
        """
        installation, created = self.get_or_create(
            installation_id=installation_id,
            defaults={
                "target_id": target_id,
                "target_type": target_type,
                "extra_data": extra_data or {},
            },
        )
        # NOTE: An installation can't change its target_id or target_type.
        # This should never happen, unless this assumption is wrong.
        if installation.target_id != target_id or installation.target_type != target_type:
            log.exception(
                "Installation target_id or target_type changed. This shouldn't happen -- look into it",
                installation_id=installation.installation_id,
                target_id=installation.target_id,
                target_type=installation.target_type,
                new_target_id=target_id,
                new_target_type=target_type,
            )
            installation.target_id = target_id
            installation.target_type = target_type
            installation.save()
        return installation, created


class GitHubAccountType(models.TextChoices):
    USER = "User", _("User")
    ORGANIZATION = "Organization", _("Organization")


class GitHubAppInstallation(TimeStampedModel):
    installation_id = models.PositiveBigIntegerField(
        help_text=_("The application installation ID"),
        unique=True,
        db_index=True,
    )
    target_id = models.PositiveBigIntegerField(
        help_text=_("A GitHub account ID, it can be from a user or an organization"),
    )
    target_type = models.CharField(
        help_text=_("Account type that the target_id belongs to (user or organization)"),
        choices=GitHubAccountType,
        max_length=255,
    )
    extra_data = models.JSONField(
        help_text=_("Extra data returned by the webhook when the installation is created"),
        default=dict,
    )

    objects = GitHubAppInstallationManager()

    class Meta(TimeStampedModel.Meta):
        verbose_name = _("GitHub app installation")

    @cached_property
    def service(self):
        """Return the service for this installation."""
        from readthedocs.oauth.services import GitHubAppService

        return GitHubAppService(self)

    @property
    def url(self):
        """Return the URL to the GitHub App installation page."""
        return f"https://github.com/apps/{settings.GITHUB_APP_NAME}/installations/{self.installation_id}"

    def delete(self, *args, **kwargs):
        """Override delete method to remove orphaned remote organizations."""
        self.delete_repositories()
        return super().delete(*args, **kwargs)

    def delete_repositories(self, repository_ids: list[int] | None = None):
        """
        Delete repositories linked to this installation.
        When an installation is deleted, we delete all its remote repositories
        and relations, users will need to manually link the projects to each repository again.
        We also remove organizations that don't have any repositories after removing the repositories.
        :param repository_ids: List of repository ids (remote ID) to delete.
         If None, all repositories will be considered for deletion.
        """
        # repository_ids is optional (None, which means all repositories),
        # but if it's an empty list, we don't want to delete anything.
        if repository_ids is not None and not repository_ids:
            log.info("No remote repositories to delete")
            return

        remote_organizations = RemoteOrganization.objects.filter(
            repositories__github_app_installation=self,
            vcs_provider=GITHUB_APP,
        )
        remote_repositories = self.repositories.filter(vcs_provider=GITHUB_APP)
        if repository_ids:
            remote_organizations = remote_organizations.filter(
                repositories__remote_id__in=repository_ids
            )
            remote_repositories = remote_repositories.filter(remote_id__in=repository_ids)

        # Fetch all IDs before deleting the repositories, so we can filter the organizations later.
        remote_organizations_ids = list(remote_organizations.values_list("id", flat=True))

        count, deleted = remote_repositories.delete()
        log.info(
            "Deleted remote repositories that our app no longer has access to",
            count=count,
            deleted=deleted,
            installation_id=self.installation_id,
            target_id=self.target_id,
            target_type=self.target_type,
        )

        count, deleted = RemoteOrganization.objects.filter(
            id__in=remote_organizations_ids,
            repositories=None,
        ).delete()
        log.info(
            "Deleted orphaned remote organizations",
            count=count,
            deleted=deleted,
            installation_id=self.installation_id,
            target_id=self.target_id,
            target_type=self.target_type,
        )

    def delete_organization(self, organization_id: int):
        """Delete a remote organization and all its remote repositories and relations from the database."""
        count, deleted = RemoteOrganization.objects.filter(
            remote_id=str(organization_id),
            vcs_provider=GITHUB_APP,
        ).delete()
        log.info(
            "Deleted remote organization",
            count=count,
            deleted=deleted,
            organization_id=organization_id,
            installation_id=self.installation_id,
            target_id=self.target_id,
            target_type=self.target_type,
        )


class RemoteOrganization(TimeStampedModel):
    """
    Organization from remote service.

    This encapsulates both Github and Bitbucket
    """

    users = models.ManyToManyField(
        User,
        verbose_name=_("Users"),
        related_name="oauth_organizations",
        through="RemoteOrganizationRelation",
    )
    slug = models.CharField(_("Slug"), max_length=255)
    name = models.CharField(_("Name"), max_length=255, null=True, blank=True)
    email = models.EmailField(_("Email"), max_length=255, null=True, blank=True)
    avatar_url = models.URLField(
        _("Avatar image URL"),
        null=True,
        blank=True,
        max_length=255,
    )
    url = models.URLField(
        _("URL to organization page"),
        max_length=200,
        null=True,
        blank=True,
    )
    # VCS provider organization id
    remote_id = models.CharField(db_index=True, max_length=128)
    vcs_provider = models.CharField(_("VCS provider"), choices=VCS_PROVIDER_CHOICES, max_length=32)

    objects = RemoteOrganizationQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        unique_together = (
            "remote_id",
            "vcs_provider",
        )
        db_table = "oauth_remoteorganization_2020"

    def __str__(self):
        return self.slug

    def get_remote_organization_relation(self, user, social_account):
        """Return RemoteOrganizationRelation object for the remote organization."""
        (
            remote_organization_relation,
            _,
        ) = RemoteOrganizationRelation.objects.get_or_create(
            remote_organization=self, user=user, account=social_account
        )
        return remote_organization_relation


class RemoteOrganizationRelation(TimeStampedModel):
    remote_organization = models.ForeignKey(
        RemoteOrganization,
        related_name="remote_organization_relations",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User, related_name="remote_organization_relations", on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_("Connected account"),
        related_name="remote_organization_relations",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = (
            "remote_organization",
            "account",
        )


class RemoteRepository(TimeStampedModel):
    """
    Remote importable repositories.

    This models Github and Bitbucket importable repositories
    """

    # This should now be a OneToOne
    users = models.ManyToManyField(
        User,
        verbose_name=_("Users"),
        related_name="oauth_repositories",
        through="RemoteRepositoryRelation",
    )
    organization = models.ForeignKey(
        RemoteOrganization,
        verbose_name=_("Organization"),
        related_name="repositories",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("Name"), max_length=255)
    full_name = models.CharField(
        _("Full Name"),
        max_length=255,
        db_index=True,
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Description of the project"),
    )
    avatar_url = models.URLField(
        _("Owner avatar image URL"),
        null=True,
        blank=True,
        max_length=255,
    )

    ssh_url = models.URLField(
        _("SSH URL"),
        max_length=512,
        blank=True,
        validators=[URLValidator(schemes=["ssh"])],
    )
    clone_url = models.URLField(
        _("Repository clone URL"),
        max_length=512,
        blank=True,
        validators=[
            URLValidator(schemes=["http", "https", "ssh", "git"]),
        ],
    )
    html_url = models.URLField(_("HTML URL"), null=True, blank=True)

    private = models.BooleanField(_("Private repository"), default=False)
    vcs = models.CharField(
        _("vcs"),
        max_length=200,
        blank=True,
        choices=REPO_CHOICES,
    )
    default_branch = models.CharField(
        _("Default branch of the repository"),
        max_length=150,
        null=True,
        blank=True,
    )
    # VCS provider repository id
    remote_id = models.CharField(max_length=128)
    vcs_provider = models.CharField(_("VCS provider"), choices=VCS_PROVIDER_CHOICES, max_length=32)

    github_app_installation = models.ForeignKey(
        GitHubAppInstallation,
        verbose_name=_("GitHub App Installation"),
        related_name="repositories",
        null=True,
        blank=True,
        # When an installation is deleted, we delete all its remote repositories
        # and relations, users will need to manually link the projects to each repository again.
        on_delete=models.CASCADE,
    )

    objects = RemoteRepositoryQuerySet.as_manager()

    class Meta:
        ordering = ["full_name"]
        verbose_name_plural = "remote repositories"
        unique_together = (
            "remote_id",
            "vcs_provider",
        )
        db_table = "oauth_remoterepository_2020"

    def __str__(self):
        return self.html_url or self.full_name

    def matches(self, user):
        """Existing projects connected to this RemoteRepository."""

        # TODO: remove this method and refactor the API response in ``/api/v2/repos/``
        # (or v3) to just return the linked Project (slug, url) if the ``RemoteRepository``
        # connection exists. Note the frontend needs to be simplified as well in
        # ``import.js`` and ``project_import.html``.

        projects = (
            Project.objects.public(user)
            .filter(
                remote_repository=self,
            )
            .values("slug")
        )

        return [
            {
                "id": project["slug"],
                "url": reverse(
                    "projects_detail",
                    kwargs={
                        "project_slug": project["slug"],
                    },
                ),
            }
            for project in projects
        ]

    def get_remote_repository_relation(self, user, social_account):
        """Return RemoteRepositoryRelation object for the remote repository."""
        remote_repository_relation, _ = RemoteRepositoryRelation.objects.get_or_create(
            remote_repository=self, user=user, account=social_account
        )
        return remote_repository_relation

    def get_service_class(self):
        from readthedocs.oauth.services import registry

        for service_cls in registry:
            if service_cls.vcs_provider_slug == self.vcs_provider:
                return service_cls

        # NOTE: this should never happen, but we log it just in case
        log.exception("Service not found for the VCS provider", vcs_provider=self.vcs_provider)
        return None


class RemoteRepositoryRelation(TimeStampedModel):
    remote_repository = models.ForeignKey(
        RemoteRepository,
        related_name="remote_repository_relations",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User, related_name="remote_repository_relations", on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        SocialAccount,
        verbose_name=_("Connected account"),
        related_name="remote_repository_relations",
        on_delete=models.CASCADE,
    )
    admin = models.BooleanField(_("Has admin privilege"), default=False)

    class Meta:
        unique_together = (
            "remote_repository",
            "account",
        )
