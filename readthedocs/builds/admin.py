"""Django admin interface for `~builds.models.Build` and related models.
"""

from django.contrib import admin
from builds.models import Build, VersionAlias, Version
from guardian.admin import GuardedModelAdmin

class BuildAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'success', 'type', 'state')

class VersionAdmin(GuardedModelAdmin):
    search_fields = ('slug', 'project__name')
    list_filter = ('project', 'privacy_level')

admin.site.register(Build, BuildAdmin)
admin.site.register(VersionAlias)
admin.site.register(Version, VersionAdmin)
