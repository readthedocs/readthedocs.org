"""Domain Admin classes."""
from django.contrib import admin

from .models import SphinxDomain


class SphinxDomainAdmin(admin.ModelAdmin):
    list_filter = ('type',)
    raw_id_fields = ('project', 'version')
    search_fields = ('doc_name', 'name')
    readonly_fields = ('created', 'modified')


admin.site.register(SphinxDomain, SphinxDomainAdmin)
