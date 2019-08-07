"""SearchQuery Admin classes."""

from django.contrib import admin

from .models import SearchQuery


class SearchQueryAdmin(admin.ModelAdmin):
    list_filter = ('created',)
    list_display = ('__str__', 'created')
    search_fields = ('project__slug', 'version__slug', 'query')
    readonly_fields = ('created', 'modified')
    list_select_related = ('project', 'version', 'version__project')


admin.site.register(SearchQuery, SearchQueryAdmin)
