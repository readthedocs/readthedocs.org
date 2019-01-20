"""Django admin interface for `~builds.models.Build` and related models."""

from __future__ import absolute_import

from django.contrib import admin, messages

from readthedocs.builds.models import Build, Version, BuildCommandResult
from readthedocs.restapi.utils import get_delete_query
from readthedocs.search.utils import reindex_version, unindex_via_query
from guardian.admin import GuardedModelAdmin


class BuildCommandResultInline(admin.TabularInline):
    model = BuildCommandResult
    fields = ('command', 'exit_code', 'output')


class BuildAdmin(admin.ModelAdmin):
    fields = ('project', 'version', 'type', 'state', 'error', 'success', 'length', 'cold_storage')
    list_display = ('id', 'project', 'version_name', 'success', 'type', 'state', 'date')
    list_filter = ('type', 'state', 'success')
    list_select_related = ('project', 'version')
    raw_id_fields = ('project', 'version')
    inlines = (BuildCommandResultInline,)
    search_fields = ('project__name', 'version__slug')

    def version_name(self, obj):
        return obj.version.verbose_name


class VersionAdmin(GuardedModelAdmin):
    search_fields = ('slug', 'project__name')
    list_display = ('slug', 'type', 'project', 'privacy_level', 'active', 'built')
    list_filter = ('type', 'privacy_level', 'active', 'built')
    raw_id_fields = ('project',)
    actions = ['reindex', 'wipe_index']

    def reindex(self, request, queryset):
        """Reindex all selected versions"""
        qs_iterator = queryset.iterator()
        for version in qs_iterator:
            success, err_msg = reindex_version(version)
            if success:
                self.message_user(
                    request,
                    'Reindexing triggered for {}'.format(version.slug),
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    'Reindexing failed for {}. {}'.format(version.slug, err_msg),
                    level=messages.ERROR
                )

    reindex.short_description = 'Reindex selected versions'

    def wipe_index(self, request, queryset):
        """Wipe index of selected versions"""
        qs_iterator = queryset.iterator()
        for version in qs_iterator:
            query = get_delete_query(version_slug=version.slug)
            success, err_msg = unindex_via_query(query)
            if success:
                self.message_user(
                    request,
                    'Index wiped for {}'.format(version.slug),
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    'Error in wiping index for {}. {}'.format(version.slug, err_msg),
                    level=messages.ERROR
                )

    wipe_index.short_description = 'Wipe index of selected versions'


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
