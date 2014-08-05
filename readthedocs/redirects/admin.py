from django.contrib import admin
from models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = ['from_url', 'to_url', 'http_status', 'status']

admin.site.register(Redirect, RedirectAdmin)
