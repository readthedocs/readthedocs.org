from django.contrib import admin

from .models import OAuthRepository, OAuthOrganization


class OAuthRepositoryAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class OAuthOrganizationAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


admin.site.register(OAuthRepository, OAuthRepositoryAdmin)
admin.site.register(OAuthOrganization, OAuthOrganizationAdmin)
