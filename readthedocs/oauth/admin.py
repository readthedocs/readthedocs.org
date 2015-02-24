from django.contrib import admin
from .models import GithubProject, GithubOrganization, BitbucketProject, BitbucketTeam


class GithubProjectAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class GithubOrganizationAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class BitbucketProjectAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)


class BitBucketTeamAdmin(admin.ModelAdmin):
    raw_id_fields = ('users',)

admin.site.register(GithubOrganization, GithubOrganizationAdmin)
admin.site.register(GithubProject, GithubProjectAdmin)
admin.site.register(BitbucketTeam, BitBucketTeamAdmin)
admin.site.register(BitbucketProject, BitbucketProjectAdmin)
