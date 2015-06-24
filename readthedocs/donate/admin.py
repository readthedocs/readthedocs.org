from django.contrib import admin
from .models import Supporter

class SupporterAdmin(admin.ModelAdmin):
    model = Supporter
    raw_id_fields = ('user',)
    list_display = ('name', 'email', 'dollars', 'public')
    list_filter = ('name', 'email', 'dollars', 'public')

admin.site.register(Supporter, SupporterAdmin)

