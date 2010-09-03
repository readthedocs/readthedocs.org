"""Django admin interface for `~bookmarks.models.Bookmark`.
"""

from django.contrib import admin
from bookmarks.models import Bookmark

class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'url')

admin.site.register(Bookmark, BookmarkAdmin)
