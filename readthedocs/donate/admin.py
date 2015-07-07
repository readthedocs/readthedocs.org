from django.contrib import admin
from .models import Supporter, SupporterPromo


class SupporterAdmin(admin.ModelAdmin):
    model = Supporter
    raw_id_fields = ('user',)
    list_display = ('name', 'email', 'dollars', 'public')
    list_filter = ('name', 'email', 'dollars', 'public')


class SupporterPromoAdmin(admin.ModelAdmin):
    model = SupporterPromo
    list_display = ('name', 'display_type', 'text', 'live')
    list_filter = ('live', 'display_type')


admin.site.register(Supporter, SupporterAdmin)
admin.site.register(SupporterPromo, SupporterPromoAdmin)
