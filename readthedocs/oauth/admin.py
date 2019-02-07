# -*- coding: utf-8 -*-

"""Admin configuration for the OAuth app."""

from django.contrib import admin

from .models import RemoteOrganization, RemoteRepository


class RemoteRepositoryAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteRepository model."""

    raw_id_fields = ('users',)


class RemoteOrganizationAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteOrganization model."""

    raw_id_fields = ('users',)


admin.site.register(RemoteRepository, RemoteRepositoryAdmin)
admin.site.register(RemoteOrganization, RemoteOrganizationAdmin)
