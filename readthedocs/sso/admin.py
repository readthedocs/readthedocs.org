"""Admin interface for SSO models."""

from django.contrib import admin

from .models import SSODomain, SSOIntegration

admin.site.register(SSOIntegration)
admin.site.register(SSODomain)
