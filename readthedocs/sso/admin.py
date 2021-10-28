"""Admin interface for SSO models."""
import logging

from django.contrib import admin, messages

from readthedocs.core.permissions import AdminPermission
from readthedocs.oauth.tasks import sync_remote_repositories

from .models import SSODomain, SSOIntegration


log = logging.getLogger(__name__)


class SSOIntegrationAdmin(admin.ModelAdmin):

    """Admin configuration for SSOIntegration."""

    list_display = ('organization', 'provider')
    search_fields = ('organization__slug', 'organization__name', 'domains__domain')
    list_filter = ('provider',)

    actions = [
        'resync_sso_user_accounts',
    ]

    def resync_sso_user_accounts(self, request, queryset):  # pylint: disable=no-self-use
        users_count = 0
        organizations_count = queryset.count()

        for ssointegration in queryset.select_related('organization'):
            members = AdminPermission.members(ssointegration.organization)
            log.info(
                'Triggering SSO re-sync for organization. organization=%s users=%s',
                ssointegration.organization.slug,
                members.count(),
            )
            users_count += members.count()
            for user in members:
                sync_remote_repositories.delay(user.pk)

        messages.add_message(
            request,
            messages.INFO,
            f'Triggered resync for {organizations_count} organizations and {users_count} users.'
        )

    resync_sso_user_accounts.short_description = 'Re-sync all SSO user accounts'


admin.site.register(SSOIntegration, SSOIntegrationAdmin)
admin.site.register(SSODomain)
