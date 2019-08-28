"""SearchQuery Admin classes."""

from django.contrib import admin

from .models import SearchQuery, PageView


class SearchQueryAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'version')
    list_filter = ('created',)
    list_display = ('__str__', 'created')
    search_fields = ('project__slug', 'version__slug', 'query')
    readonly_fields = ('created', 'modified')
    list_select_related = ('project', 'version', 'version__project')


class PageViewAdmin(admin.ModelAdmin):
    raw_id_fields = ('project', 'version')
    list_display = ('__str__', 'view_count')
    search_fields = ('project__slug', 'version__slug', 'path')
    readonly_fields = ('created', 'modified')
    list_select_related = ('project', 'version', 'version__project')


admin.site.register(SearchQuery, SearchQueryAdmin)
admin.site.register(PageView, PageViewAdmin)
