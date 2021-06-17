# -*- coding: utf-8 -*-

"""Admin configuration for the OAuth app."""

from django.contrib import admin

from .models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)


class RemoteRepositoryAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteRepository model."""

    raw_id_fields = ('organization',)


class RemoteRepositoryRelationAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteRepositoryRelation model."""

    raw_id_fields = ('account', 'remote_repository', 'user',)
    list_select_related = ('remote_repository', 'user',)


class RemoteOrganizationRelationAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteOrganizationRelation model."""

    raw_id_fields = ('account', 'remote_organization', 'user',)
    list_select_related = ('remote_organization', 'user',)


admin.site.register(RemoteRepository, RemoteRepositoryAdmin)
admin.site.register(RemoteRepositoryRelation, RemoteRepositoryRelationAdmin)
admin.site.register(RemoteOrganization)
admin.site.register(RemoteOrganizationRelation, RemoteOrganizationRelationAdmin)
