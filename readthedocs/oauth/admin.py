"""Admin configuration for the OAuth app."""

from django import urls
from django.contrib import admin
from django.utils.html import format_html

from .models import GitHubAppInstallation
from .models import RemoteOrganization
from .models import RemoteOrganizationRelation
from .models import RemoteRepository
from .models import RemoteRepositoryRelation


@admin.register(GitHubAppInstallation)
class GitHubAppInstallationAdmin(admin.ModelAdmin):
    list_display = (
        "installation_id",
        "target_type",
        "target_id",
    )


@admin.register(RemoteRepository)
class RemoteRepositoryAdmin(admin.ModelAdmin):
    """Admin configuration for the RemoteRepository model."""

    readonly_fields = (
        "created",
        "modified",
        "remote_repository_relations",
    )
    raw_id_fields = ("organization", "github_app_installation")
    list_select_related = ("organization",)
    list_filter = (
        "vcs_provider",
        "vcs",
        "private",
    )
    search_fields = (
        "name",
        "full_name",
        "remote_id",
        "projects__slug",
        "projects__name",
    )
    list_display = (
        "id",
        "full_name",
        "html_url",
        "private",
        "organization",
        "get_vcs_provider_display",
        "get_vcs_display",
    )

    @admin.display(description="Remote repository relations")
    def remote_repository_relations(self, obj):
        """Link to relation objects filtered to this remote repository."""
        if not obj.pk:
            return "-"

        url = urls.reverse(
            "admin:{}_{}_changelist".format(
                RemoteRepositoryRelation._meta.app_label,
                RemoteRepositoryRelation._meta.model_name,
            ),
        )
        relation_count = obj.remote_repository_relations.count()
        relation_label = "relation" if relation_count == 1 else "relations"
        return format_html(
            '<a href="{}?{}={}">{} remote repository {}</a>',
            url,
            "remote_repository__id__exact",
            obj.pk,
            relation_count,
            relation_label,
        )


@admin.register(RemoteOrganization)
class RemoteOrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for the RemoteOrganization model."""

    readonly_fields = (
        "created",
        "modified",
    )
    search_fields = (
        "name",
        "slug",
        "email",
        "url",
        "remote_id",
    )
    list_filter = ("vcs_provider",)
    list_display = (
        "id",
        "name",
        "slug",
        "email",
        "get_vcs_provider_display",
    )


@admin.register(RemoteRepositoryRelation)
class RemoteRepositoryRelationAdmin(admin.ModelAdmin):
    """Admin configuration for the RemoteRepositoryRelation model."""

    raw_id_fields = (
        "account",
        "remote_repository",
        "user",
    )
    list_select_related = (
        "remote_repository",
        "user",
        "account",
    )
    list_display = (
        "id",
        "remote_repository",
        "user",
        "account",
        "vcs_provider",
        "admin",
    )
    list_filter = (
        "remote_repository__vcs_provider",
        "admin",
    )
    search_fields = (
        "remote_repository__name",
        "remote_repository__full_name",
        "remote_repository__remote_id",
        "remote_repository__projects__slug",
        "remote_repository__projects__name",
    )

    def vcs_provider(self, obj):
        """Get the display name for the VCS provider."""
        return obj.remote_repository.vcs_provider


@admin.register(RemoteOrganizationRelation)
class RemoteOrganizationRelationAdmin(admin.ModelAdmin):
    """Admin configuration for the RemoteOrganizationRelation model."""

    raw_id_fields = (
        "account",
        "remote_organization",
        "user",
    )
    list_select_related = (
        "remote_organization",
        "user",
        "account",
    )
    list_display = (
        "id",
        "remote_organization",
        "user",
        "account",
        "vcs_provider",
    )
    list_filter = ("remote_organization__vcs_provider",)

    def vcs_provider(self, obj):
        """Get the display name for the VCS provider."""
        return obj.remote_organization.vcs_provider
