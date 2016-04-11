"""Django administration interface for `projects.models`"""

from readthedocs.builds.models import Version
from django.contrib import admin
from readthedocs.redirects.models import Redirect
from .models import (Project, ImportedFile,
                     ProjectRelationship, EmailHook, WebHook, Domain)
from guardian.admin import GuardedModelAdmin

from readthedocs.donate.models import ProjectImpressions


class ProjectRelationshipInline(admin.TabularInline):

    """Project inline relationship view for :py:cls:`ProjectAdmin`"""

    model = ProjectRelationship
    fk_name = 'parent'
    raw_id_fields = ('child',)


class VersionInline(admin.TabularInline):

    """Version inline relationship view for :py:cls:`ProjectAdmin`"""

    model = Version


class RedirectInline(admin.TabularInline):

    """Redirect inline relationship view for :py:cls:`ProjectAdmin`"""

    model = Redirect


class DomainInline(admin.TabularInline):
    model = Domain


class ImpressionInline(admin.TabularInline):
    model = ProjectImpressions
    readonly_fields = ('date', 'promo', 'offers', 'views', 'clicks', 'view_ratio', 'click_ratio')
    extra = 0
    can_delete = False
    max_num = 15

    def view_ratio(self, instance):
        return instance.view_ratio * 100

    def click_ratio(self, instance):
        return instance.click_ratio * 100


class ProjectAdmin(GuardedModelAdmin):

    """Project model admin view"""

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'repo', 'repo_type', 'allow_comments', 'featured', 'theme')
    list_filter = ('repo_type', 'allow_comments', 'featured', 'privacy_level',
                   'documentation_type', 'programming_language')
    list_editable = ('featured',)
    search_fields = ('slug', 'repo')
    inlines = [ProjectRelationshipInline, RedirectInline,
               VersionInline, DomainInline, ImpressionInline]
    raw_id_fields = ('users', 'main_language_project')


class ImportedFileAdmin(admin.ModelAdmin):

    """Admin view for :py:cls:`ImportedFile`"""

    list_display = ('path', 'name', 'version')


class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'project', 'count')
    search_fields = ('domain', 'project__slug')
    raw_id_fields = ('project',)
    list_filter = ('canonical',)
    model = Domain

admin.site.register(Project, ProjectAdmin)
admin.site.register(ImportedFile, ImportedFileAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(EmailHook)
admin.site.register(WebHook)
