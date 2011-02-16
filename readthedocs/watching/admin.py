"""Django admin interface for `~watching.models.PageView`.
"""

from watching.models import PageView
from django.contrib import admin

class PageViewAdmin(admin.ModelAdmin):
    list_display=('project', 'url','count')

admin.site.register(PageView, PageViewAdmin)
