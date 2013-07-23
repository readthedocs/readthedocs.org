from django.contrib import admin
from .models import SphinxComment, SphinxNode

class SphinxNodeAdmin(admin.ModelAdmin):
    search_fields = ('id', 'document')
    list_filter = ('project__name',)

class SphinxCommentAdmin(admin.ModelAdmin):
    search_fields = ('text',)

admin.site.register(SphinxNode, SphinxNodeAdmin)
admin.site.register(SphinxComment, SphinxCommentAdmin)
