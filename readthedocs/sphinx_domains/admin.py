"""Domain Admin classes."""
from django.contrib import admin

from .models import SphinxDomain


class SphinxDomainAdmin(admin.ModelAdmin):
    list_filter = ('type',)
    list_display = ('__str__', 'version', 'build')
    search_fields = ('doc_name', 'name', 'project__slug', 'version__slug', 'build')
    readonly_fields = ('created', 'modified')
    raw_id_fields = ('project', 'version', 'html_file')
    list_select_related = ('project', 'version', 'version__project')


admin.site.register(SphinxDomain, SphinxDomainAdmin)
