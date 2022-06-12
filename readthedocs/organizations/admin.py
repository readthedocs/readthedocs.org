"""Django admin interface for organization models."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from readthedocs.oauth.tasks import sync_remote_repositories
from readthedocs.organizations.models import Organization


class OrganizationAdmin(admin.ModelAdmin):

    """Admin configuration for Organization."""

    readonly_fields = (
        "pub_date",
        "modified_date",
        "slug",
    )
    list_display = (
        "id",
        "name",
        "max_concurrent_builds",
        "disabled",
        "artifacts_cleaned",
        "modified_date",
        "pub_date",
    )
    list_filter = (
        "disabled",
        "artifacts_cleaned",
    )
    raw_id_fields = (
        "projects",
        "owners",
    )
    search_fields = (
        "projects__slug",
        "owners__username",
        "owners__email",
        "name",
        "slug",
        "email",
        "url",
        "stripe_id",
    )
    actions = ("sync_remote_repositories_action",)

    def sync_remote_repositories_action(self, request, queryset):
        """Resync remote repositories for all members of the selected organizations."""
        formatted_task_urls = []

        users = (
            User.objects.filter(
                Q(teams__organization__in=queryset)
                | Q(owner_organizations__in=queryset),
            )
            .values_list("id", "username")
            .distinct()
        )

        for user_id, username in users:
            result = sync_remote_repositories.delay(user_id=user_id)
            job_status_url = reverse(
                "api_job_status", kwargs={"task_id": result.task_id}
            )
            formatted_task_urls.append(
                format_html("<a href='{}'>{} task</a>", job_status_url, username)
            )

        self.message_user(
            request,
            mark_safe(
                "Following sync remote repository tasks were "
                "triggered: {}".format(", ".join(formatted_task_urls))
            ),
        )

    sync_remote_repositories_action.short_description = "Sync remote repositories"


admin.site.register(Organization, OrganizationAdmin)
