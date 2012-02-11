"""Django admin interface for `~builds.models.Build` and related models.
"""

from django.contrib import admin
from builds.models import Build, VersionAlias, Version

class BuildAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'success', 'state')

admin.site.register(Build, BuildAdmin)
admin.site.register(VersionAlias)
admin.site.register(Version)
