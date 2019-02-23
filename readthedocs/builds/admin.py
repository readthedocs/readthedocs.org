# -*- coding: utf-8 -*-

"""Django admin interface for `~builds.models.Build` and related models."""

from django.contrib import admin, messages
from guardian.admin import GuardedModelAdmin

from readthedocs.builds.models import Build, BuildCommandResult, Version
from readthedocs.core.utils import trigger_build
from readthedocs.projects.models import HTMLFile
from readthedocs.search.utils import _indexing_helper


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
    actions = ['build_version', 'reindex_version', 'wipe_version']

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

    def reindex_version(self, request, queryset):
        """Reindexes all selected versions to ES."""
        for version in queryset.iterator():
            html_objs = HTMLFile.objects.filter(project=version.project, version=version)
            _indexing_helper(html_objs, wipe=False)

        self.message_user(
            request,
            'Task initiated successfully',
            messages.SUCCESS
        )

    reindex_version.short_description = 'Reindex version'

    def wipe_version(self, request, queryset):
        """Wipe selected versions from ES."""
        for version in queryset.iterator():
            html_objs = HTMLFile.objects.filter(project=version.project, version=version)
            _indexing_helper(html_objs, wipe=True)

        self.message_user(
            request,
            'Task initiated successfully',
            messages.SUCCESS,
        )

    wipe_version.short_description = 'Wipe version'


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
