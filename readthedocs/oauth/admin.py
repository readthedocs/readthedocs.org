"""Admin configuration for the OAuth app."""

from django.contrib import admin

from readthedocs.projects.models import Project

from .models import GitHubAppInstallation
from .models import RemoteOrganization
from .models import RemoteOrganizationRelation
from .models import RemoteRepository
from .models import RemoteRepositoryRelation


class ProjectInline(admin.TabularInline):
    """Project inline for :py:class:`RemoteRepositoryAdmin`."""

    model = Project
    fk_name = "remote_repository"
    fields = ("slug", "name", "repo")
    readonly_fields = ("slug", "name", "repo")
    show_change_link = True
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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

    inlines = [ProjectInline]
    readonly_fields = (
        "created",
        "modified",
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
