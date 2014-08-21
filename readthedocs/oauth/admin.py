from django.contrib import admin
from .models import GithubProject, GithubOrganization

admin.site.register(GithubProject)
admin.site.register(GithubOrganization)
