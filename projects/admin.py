"""Django administration interface for `~projects.models.Project`
and related models.
"""

from builds.models import Version
from django.contrib import admin
from projects.models import Project, File, ImportedFile



class VersionInline(admin.TabularInline):
    model = Version


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'repo', 'repo_type', 'theme', 'status')
    search_fields = ('name', 'repo')
    list_filter = ('repo_type', 'status')
    inlines = [VersionInline]


class FileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Project, ProjectAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(ImportedFile)
