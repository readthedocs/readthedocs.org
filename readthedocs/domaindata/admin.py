from django.contrib import admin
from .models import DomainData


class DomainDataAdmin(admin.ModelAdmin):
    list_filter = ('type', 'project')


admin.site.register(DomainData, DomainDataAdmin)
