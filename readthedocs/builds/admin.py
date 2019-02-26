# -*- coding: utf-8 -*-

"""Django admin interface for `~builds.models.Build` and related models."""

from django.contrib import admin, messages
from guardian.admin import GuardedModelAdmin

from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.general import wipe_version_via_slugs


class BuildCommandResultInline(admin.TabularInline):
    model = BuildCommandResult
    fields = ('command', 'exit_code', 'output')


class BuildAdmin(admin.ModelAdmin):
    fields = (
        'project',
        'version',
        'type',
        'state',
        'error',
        'success',
        'length',
        'cold_storage',
    )
    list_display = (
        'id',
        'project',
        'version_name',
        'success',
        'type',
        'state',
        'date',
    )
    list_filter = ('type', 'state', 'success')
    list_select_related = ('project', 'version')
    raw_id_fields = ('project', 'version')
    inlines = (BuildCommandResultInline,)
    search_fields = ('project__name', 'version__slug')

    def version_name(self, obj):
        return obj.version.verbose_name


class VersionAdmin(GuardedModelAdmin):
    search_fields = ('slug', 'project__name')
    list_display = (
        'slug',
        'type',
        'project',
        'privacy_level',
        'active',
        'built',
    )
    list_filter = ('type', 'privacy_level', 'active', 'built')
    search_fields = ('slug', 'project__slug')
    raw_id_fields = ('project',)
    actions = ['wipe_selected_versions', 'build_version']

    def wipe_selected_versions(self, request, queryset):
        """Wipes the selected versions."""
        for version in queryset:
            wipe_version_via_slugs(
                version_slug=version.slug,
                project_slug=version.project.slug
            )
            self.message_user(
                request,
                'Wiped {}.'.format(version.slug),
                level=messages.SUCCESS
            )

    wipe_selected_versions.short_description = 'Wipe selected versions'

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
            'Triggered builds for {} version(s).'.format(total),
        )

    build_version.short_description = 'Build version'


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
