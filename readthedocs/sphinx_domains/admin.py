"""Domain Admin classes."""
from django.contrib import admin

from .models import SphinxDomain


class SphinxDomainAdmin(admin.ModelAdmin):
    list_filter = ('type',)
    list_display = ('docs_url', 'version', 'build')
    raw_id_fields = ('project', 'version')
    search_fields = ('doc_name', 'name', 'project__slug', 'version__slug', 'build')
    readonly_fields = ('created', 'modified')


admin.site.register(SphinxDomain, SphinxDomainAdmin)
