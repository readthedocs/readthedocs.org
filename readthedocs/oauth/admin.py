from django.contrib import admin
from .models import GithubProject, GithubOrganization


class GithubProjectAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class GithubOrganizationAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)

admin.site.register(GithubOrganization, GithubOrganizationAdmin)
admin.site.register(GithubProject, GithubProjectAdmin)
