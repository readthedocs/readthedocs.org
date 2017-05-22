"""Django admin interface for `~bookmarks.models.Bookmark`."""
from __future__ import absolute_import, division, print_function

from django.contrib import admin
from readthedocs.bookmarks.models import Bookmark


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('project', 'date', 'url')

admin.site.register(Bookmark, BookmarkAdmin)
