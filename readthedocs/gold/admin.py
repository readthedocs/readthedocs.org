# -*- coding: utf-8 -*-

"""Django admin configuration for the Gold Membership app."""

from django.contrib import admin

from .models import GoldUser


class GoldAdmin(admin.ModelAdmin):
    model = GoldUser
    raw_id_fields = ('user', 'projects')
    list_display = ('user', 'level', 'modified_date', 'subscribed')
    list_filter = ('level',)


admin.site.register(GoldUser, GoldAdmin)
