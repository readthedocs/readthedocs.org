from django.contrib import admin

from projects.models import Project, File


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'repo', 'repo_type', 'theme', 'status', 'whitelisted')
    search_fields = ('name', 'repo')
    list_filter = ('repo_type', 'whitelisted', 'status')


class FileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Project, ProjectAdmin)
admin.site.register(File, FileAdmin)
