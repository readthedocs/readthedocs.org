from django.contrib import admin

from .models import SSOIntegration, SSODomain

admin.site.register(SSOIntegration)
admin.site.register(SSODomain)
