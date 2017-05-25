"""Django admin configuration for the redirects app."""

from __future__ import absolute_import

from django.contrib import admin
from .models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = ['project', 'redirect_type', 'from_url', 'to_url']
    raw_id_fields = ('project',)

admin.site.register(Redirect, RedirectAdmin)
