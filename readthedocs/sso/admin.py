"""Admin interface for SSO models."""

import structlog
from django.contrib import admin
from django.contrib import messages

from readthedocs.core.permissions import AdminPermission
from readthedocs.oauth.tasks import sync_remote_repositories

from .models import SSODomain
from .models import SSOIntegration


log = structlog.get_logger(__name__)


@admin.register(SSOIntegration)
class SSOIntegrationAdmin(admin.ModelAdmin):
    """Admin configuration for SSOIntegration."""

    list_display = ("organization", "provider")
    search_fields = ("organization__slug", "organization__name", "domains__domain")
    list_filter = ("provider",)
    raw_id_fields = ("organization",)

    actions = [
        "resync_sso_user_accounts",
    ]

    @admin.action(description="Re-sync all SSO user accounts")
    def resync_sso_user_accounts(self, request, queryset):
        users_count = 0
        organizations_count = queryset.count()

        for ssointegration in queryset.select_related("organization"):
            members = AdminPermission.members(ssointegration.organization)
            log.info(
                "Triggering SSO re-sync for organization.",
                organization_slug=ssointegration.organization.slug,
                count=members.count(),
            )
            users_count += members.count()
            for user in members:
                sync_remote_repositories.delay(user.pk)

        messages.add_message(
            request,
            messages.INFO,
            f"Triggered resync for {organizations_count} organizations and {users_count} users.",
        )


admin.site.register(SSODomain)
