from django.contrib import admin

from projects.models import Project, File, Conf


class ProjectAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class FileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Project, ProjectAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Conf)
