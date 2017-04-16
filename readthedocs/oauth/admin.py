from django.contrib import admin

from .models import RemoteRepository, RemoteOrganization


class RemoteRepositoryAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class RemoteOrganizationAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


admin.site.register(RemoteRepository, RemoteRepositoryAdmin)
admin.site.register(RemoteOrganization, RemoteOrganizationAdmin)
