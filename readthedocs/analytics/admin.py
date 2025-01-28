"""Analytics Admin classes."""

from django.contrib import admin

from .models import PageView


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    raw_id_fields = ("project", "version")
    list_display = ("project", "version", "path", "view_count", "date")
    search_fields = ("project__slug", "version__slug", "path")
    readonly_fields = ("date",)
    list_select_related = ("project", "version", "version__project")
