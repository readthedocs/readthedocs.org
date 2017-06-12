"""Admin configuration for the OAuth app."""

from __future__ import absolute_import
from django.contrib import admin

from .models import RemoteRepository, RemoteOrganization


class RemoteRepositoryAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteRepository model."""

    raw_id_fields = ('users',)


class RemoteOrganizationAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteOrganization model."""

    raw_id_fields = ('users',)


admin.site.register(RemoteRepository, RemoteRepositoryAdmin)
admin.site.register(RemoteOrganization, RemoteOrganizationAdmin)
