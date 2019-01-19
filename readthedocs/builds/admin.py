"""Django admin interface for `~builds.models.Build` and related models."""

from __future__ import absolute_import

from django.contrib import admin, messages
from readthedocs.projects.tasks import update_search

from readthedocs.builds.models import Build, Version, BuildCommandResult
from readthedocs.search.indexes import PageIndex, SectionIndex
from readthedocs.restapi.utils import get_delete_query
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
            try:
                commit = version.project.vcs_repo(version.slug).commit
            except:  # noqa
                # An exception can be thrown here in production, but it's not
                # documented what the exception here is.
                commit = None

            try:
                update_search(version.pk, commit,
                              delete_non_commit_files=False)
                success_msg = 'Reindexing triggered for {}'.format(version)
                self.message_user(request, success_msg)
            except Exception as e:
                error_msg = 'Reindexing failed for {}. {}'.format(version, e)
                self.message_user(request, error_msg, level=messages.ERROR)

    reindex.short_description = 'Reindex selected versions'

    def wipe_index(self, request, queryset):
        """Wipe index of selected versions"""
        qs_iterator = queryset.iterator()
        for version in qs_iterator:
            query = get_delete_query(version_slug=version.slug)
            page_obj = PageIndex()
            section_obj = SectionIndex()
            try:
                page_obj.delete_document(body=query)
                section_obj.delete_document(body=query)
                success_msg = 'Index wiped for {}'.format(version.slug)
                self.message_user(request, success_msg, level=messages.SUCCESS)
            except Exception as e:
                fail_msg = 'Cannot wipe index for {}. {}'.format(version.slug, e)
                self.message_user(request, fail_msg, level=messages.ERROR)

    wipe_index.short_description = 'Wipe index of selected versions'


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
