from django.contrib import admin
from models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = ['project', 'redirect_type', 'from_url', 'to_url'] 

admin.site.register(Redirect, RedirectAdmin)
