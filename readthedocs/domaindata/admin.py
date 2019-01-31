from django.contrib import admin
from .models import DomainData


class DomainDataAdmin(admin.ModelAdmin):
    list_filter = ('type', 'project')
    raw_id_fields = ('project', 'version')


admin.site.register(DomainData, DomainDataAdmin)
