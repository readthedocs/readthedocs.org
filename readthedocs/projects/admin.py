"""Django administration interface for `~projects.models.Project`
and related models.
"""

from builds.models import Version
from django.contrib import admin
from projects.models import Project, File, ImportedFile, ProjectRelationship

class ProjectRelationshipInline(admin.TabularInline):
    model = ProjectRelationship
    fk_name = 'parent'

class VersionInline(admin.TabularInline):
    model = Version


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'repo', 'repo_type', 'featured', 'theme')
    list_filter = ('repo_type', 'featured')
    list_editable = ('featured',)
    search_fields = ('name', 'repo')
    inlines = [ProjectRelationshipInline, VersionInline]
    raw_id_fields = ('users',)


class FileAdmin(admin.ModelAdmin):
    pass

class ImportedFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)

admin.site.register(Project, ProjectAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(ImportedFile, ImportedFileAdmin)
