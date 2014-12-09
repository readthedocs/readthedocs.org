from django.contrib import admin
from .models import DocumentNode, DocumentComment


class DocumentNodeAdmin(admin.ModelAdmin):
    search_fields = ('id', 'document')
    list_filter = ('project__name',)
    raw_id_fields = ('project', 'version')


class DocumentCommentAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    raw_id_fields = ('node',)

admin.site.register(DocumentNode, DocumentNodeAdmin)
admin.site.register(DocumentComment, DocumentCommentAdmin)
