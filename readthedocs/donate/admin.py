from django.contrib import admin
from .models import Supporter, SupporterPromo, SupporterImpressions


class SupporterAdmin(admin.ModelAdmin):
    model = Supporter
    raw_id_fields = ('user',)
    list_display = ('name', 'email', 'dollars', 'public')
    list_filter = ('name', 'email', 'dollars', 'public')


class ImpressionInline(admin.TabularInline):
    model = SupporterImpressions
    readonly_fields = ('date', 'offers', 'views', 'clicks')


class SupporterPromoAdmin(admin.ModelAdmin):
    model = SupporterPromo
    list_display = ('name', 'display_type', 'text', 'live', 'shown')
    readonly_fields = ('shown',)
    list_filter = ('live', 'display_type')
    inlines = [ImpressionInline]


admin.site.register(Supporter, SupporterAdmin)
admin.site.register(SupporterPromo, SupporterPromoAdmin)
