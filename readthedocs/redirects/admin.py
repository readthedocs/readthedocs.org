"""Django admin configuration for the redirects app."""

from __future__ import absolute_import

from django.contrib import admin
from .models import Redirect


class RedirectAdmin(admin.ModelAdmin):
    list_display = ['project', 'redirect_type', 'from_url', 'to_url', 'status']
    list_select_related = ('project',)
    list_filter = ('redirect_type', 'status')
    raw_id_fields = ('project',)
    search_fields = (
        'project__slug',
        'from_url',
        'to_url',
    )


admin.site.register(Redirect, RedirectAdmin)
