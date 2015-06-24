from django.contrib import admin
from .models import GoldUser


class GoldAdmin(admin.ModelAdmin):
    model = GoldUser
    raw_id_fields = ('user', 'projects')
    list_display = ('user', 'level')
    list_filter = ('user', 'level')

admin.site.register(GoldUser, GoldAdmin)
