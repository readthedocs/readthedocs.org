"""Django admin interface for `~builds.models.Build` and related models."""

from django.contrib import admin
from django.contrib import messages
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicParentModelAdmin

from readthedocs.builds.models import Build
from readthedocs.builds.models import BuildCommandResult
from readthedocs.builds.models import RegexAutomationRule
from readthedocs.builds.models import Version
from readthedocs.builds.models import VersionAutomationRule
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.admin import pretty_json_field
from readthedocs.projects.tasks.search import reindex_version


class BuildCommandResultInline(admin.TabularInline):
    model = BuildCommandResult
    fields = ("command", "exit_code", "output")
    classes = ["collapse"]


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    fields = (
        "project",
        "version",
        "type",
        "state",
        "error",
        "success",
        "cold_storage",
        "date",
        "builder",
        "length",
        "readthedocs_yaml_path",
        "pretty_config",
    )
    readonly_fields = (
        "date",  # required to be read-only because it's a @property
        "pretty_config",  # required to be read-only because it's a @property
        "builder",
        "length",
    )
    list_display = (
        "id",
        "project_slug",
        "version_slug",
        "success",
        "type",
        "state",
        "date",
        "builder",
        "length",
    )
    list_filter = ("type", "state", "success")
    list_select_related = ("project", "version")
    raw_id_fields = ("project", "version")
    inlines = (BuildCommandResultInline,)
    search_fields = ("project__slug", "version__slug")

    def project_slug(self, obj):
        return obj.project.slug

    def version_slug(self, obj):
        return obj.version.slug

    @admin.display(description="Config File")
    def pretty_config(self, instance):
        return pretty_json_field(instance, "config")


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "project_slug",
        "type",
        "privacy_level",
        "active",
        "built",
    )
    readonly_fields = (
        "created",
        "modified",
        "pretty_config",  # required to be read-only because it's a @property
    )
    list_filter = ("type", "privacy_level", "active", "built")
    search_fields = ("slug", "project__slug")
    raw_id_fields = ("project",)
    actions = ["build_version", "reindex_version"]

    def project_slug(self, obj):
        return obj.project.slug

    @admin.display(description="Config File")
    def pretty_config(self, instance):
        return pretty_json_field(instance, "config")

    @admin.action(description="Build version")
    def build_version(self, request, queryset):
        """Trigger a build for the project version."""
        total = 0
        for version in queryset:
            trigger_build(
                project=version.project,
                version=version,
            )
            total += 1
        messages.add_message(
            request,
            messages.INFO,
            "Triggered builds for {} version(s).".format(total),
        )

    @admin.action(description="Reindex version to ES")
    def reindex_version(self, request, queryset):
        """Reindexes all selected versions to ES."""
        for version_id in queryset.values_list("id", flat=True).iterator():
            reindex_version.delay(version_id)

        self.message_user(request, "Task initiated successfully.", messages.SUCCESS)


@admin.register(RegexAutomationRule)
class RegexAutomationRuleAdmin(PolymorphicChildModelAdmin, admin.ModelAdmin):
    raw_id_fields = ("project",)
    readonly_fields = (
        "created",
        "modified",
    )
    base_model = RegexAutomationRule


@admin.register(VersionAutomationRule)
class VersionAutomationRuleAdmin(PolymorphicParentModelAdmin, admin.ModelAdmin):
    base_model = VersionAutomationRule
    list_display = (
        "id",
        "project",
        "priority",
        "predefined_match_arg",
        "match_arg",
        "action",
        "version_type",
    )
    child_models = (RegexAutomationRule,)
    search_fields = ("project__slug",)
    list_filter = ("action", "version_type")
