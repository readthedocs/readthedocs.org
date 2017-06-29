"""ModelAdmin configurations for comments app."""

from __future__ import absolute_import
from django.contrib import admin
from .models import DocumentNode, DocumentComment, NodeSnapshot


class SnapshotAdmin(admin.TabularInline):
    model = NodeSnapshot


class DocumentNodeAdmin(admin.ModelAdmin):
    search_fields = ('id', 'document')
    list_filter = ('project__name',)
    raw_id_fields = ('project', 'version')
    list_display = ('__unicode__', 'latest_hash', 'latest_commit')
    inlines = (SnapshotAdmin,)


class DocumentCommentAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    raw_id_fields = ('node',)

admin.site.register(DocumentNode, DocumentNodeAdmin)
admin.site.register(DocumentComment, DocumentCommentAdmin)
