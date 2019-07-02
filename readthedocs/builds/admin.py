"""Django admin interface for `~builds.models.Build` and related models."""

import json
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicParentModelAdmin,
)

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from readthedocs.builds.models import (
    Build,
    BuildCommandResult,
    RegexAutomationRule,
    Version,
    VersionAutomationRule,
)
from readthedocs.core.utils import trigger_build
from readthedocs.core.utils.general import wipe_version_via_slugs
from readthedocs.projects.models import HTMLFile
from readthedocs.search.utils import _indexing_helper


def _pretty_config(instance):
    """Function to display pretty version of our data"""

    # Convert the data to sorted, indented JSON
    response = json.dumps(instance.config, sort_keys=True, indent=2)

    # Truncate the data. Alter as needed
    response = response[:5000]

    # Get the Pygments formatter
    formatter = HtmlFormatter()

    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Safe the output
    return mark_safe(style + response)


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
        'pretty_config',
    )
    readonly_fields = (
        'pretty_config',  # required to be read-only becuase it's a @property
    )
    list_display = (
        'id',
        'project',
        'version_name',
        'success',
        'type',
        'state',
        'date',
        'length'
    )
    list_filter = ('type', 'state', 'success')
    list_select_related = ('project', 'version')
    raw_id_fields = ('project', 'version')
    inlines = (BuildCommandResultInline,)
    search_fields = ('project__slug', 'version__slug')

    def version_name(self, obj):
        return obj.version.verbose_name

    def pretty_config(self, instance):
        return _pretty_config(instance)

    pretty_config.short_description = 'Config File'


class VersionAdmin(admin.ModelAdmin):

    list_display = (
        'slug',
        'type',
        'project',
        'privacy_level',
        'active',
        'built',
    )
    readonly_fields = (
        'pretty_config',  # required to be read-only becuase it's a @property
    )
    list_filter = ('type', 'privacy_level', 'active', 'built')
    search_fields = ('slug', 'project__slug')
    raw_id_fields = ('project',)
    actions = ['build_version', 'reindex_version', 'wipe_version', 'wipe_selected_versions']

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

    def pretty_config(self, instance):
        return _pretty_config(instance)

    pretty_config.short_description = 'Config File'
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

    def reindex_version(self, request, queryset):
        """Reindexes all selected versions to ES."""
        html_objs_qs = []
        for version in queryset.iterator():
            html_objs = HTMLFile.objects.filter(project=version.project, version=version)

            if html_objs.exists():
                html_objs_qs.append(html_objs)

        if html_objs_qs:
            _indexing_helper(html_objs_qs, wipe=False)

        self.message_user(
            request,
            'Task initiated successfully.',
            messages.SUCCESS
        )

    reindex_version.short_description = 'Reindex version to ES'

    def wipe_version(self, request, queryset):
        """Wipe selected versions from ES."""
        html_objs_qs = []
        for version in queryset.iterator():
            html_objs = HTMLFile.objects.filter(project=version.project, version=version)

            if html_objs.exists():
                html_objs_qs.append(html_objs)

        if html_objs_qs:
            _indexing_helper(html_objs_qs, wipe=True)

        self.message_user(
            request,
            'Task initiated successfully',
            messages.SUCCESS,
        )

    wipe_version.short_description = 'Wipe version from ES'


@admin.register(RegexAutomationRule)
class RegexAutomationRuleAdmin(PolymorphicChildModelAdmin, admin.ModelAdmin):
    raw_id_fields = ('project',)
    base_model = RegexAutomationRule


@admin.register(VersionAutomationRule)
class VersionAutomationRuleAdmin(PolymorphicParentModelAdmin, admin.ModelAdmin):
    base_model = VersionAutomationRule
    list_display = (
        'id',
        'project',
        'priority',
        'match_arg',
        'action',
        'version_type',
    )
    child_models = (RegexAutomationRule,)


admin.site.register(Build, BuildAdmin)
admin.site.register(Version, VersionAdmin)
