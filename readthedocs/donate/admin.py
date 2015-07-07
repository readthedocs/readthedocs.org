from django.contrib import admin
from .models import Supporter, SupporterPromo


class SupporterAdmin(admin.ModelAdmin):
    model = Supporter
    raw_id_fields = ('user',)
    list_display = ('name', 'email', 'dollars', 'public')
    list_filter = ('name', 'email', 'dollars', 'public')


class SupporterPromoAdmin(admin.ModelAdmin):
    model = SupporterPromo
    list_display = ('name', 'analytics_id', 'text', 'live')
    list_filter = ('live',)


admin.site.register(Supporter, SupporterAdmin)
admin.site.register(SupporterPromo, SupporterPromoAdmin)
