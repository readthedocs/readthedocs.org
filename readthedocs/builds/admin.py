# -*- coding: utf-8 -*-

"""Django admin interface for `~builds.models.Build` and related models."""

from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from readthedocs.builds.models import Build, BuildCommandResult, Version


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
    raw_id_fields = ('project',)


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
