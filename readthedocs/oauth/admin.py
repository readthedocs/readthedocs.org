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

    readonly_fields = ('created', 'modified',)
    raw_id_fields = ('organization',)
    list_select_related = ('organization',)
    list_filter = ('vcs_provider', 'vcs', 'private',)
    search_fields = ('name', 'full_name', 'remote_id',)
    list_display = (
        'id',
        'full_name',
        'html_url',
        'private',
        'organization',
        'get_vcs_provider_display',
        'get_vcs_display',
    )


class RemoteOrganizationAdmin(admin.ModelAdmin):

    """Admin configuration for the RemoteOrganization model."""

    readonly_fields = ('created', 'modified',)
    search_fields = ('name', 'slug', 'email', 'url', 'remote_id',)
    list_filter = ('vcs_provider',)
    list_display = (
        'id',
        'name',
        'slug',
        'email',
        'get_vcs_provider_display',
    )


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
admin.site.register(RemoteOrganization, RemoteOrganizationAdmin)
admin.site.register(RemoteOrganizationRelation, RemoteOrganizationRelationAdmin)
