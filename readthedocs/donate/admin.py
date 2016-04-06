from django.contrib import admin
from .models import (Supporter, SupporterPromo,
                     PromoImpressions, GeoFilter)


class SupporterAdmin(admin.ModelAdmin):
    model = Supporter
    raw_id_fields = ('user',)
    list_display = ('name', 'email', 'dollars', 'public')
    list_filter = ('name', 'email', 'dollars', 'public')


class ImpressionInline(admin.TabularInline):
    model = PromoImpressions
    readonly_fields = ('date', 'promo', 'offers', 'views', 'clicks', 'view_ratio', 'click_ratio')
    extra = 0
    can_delete = False
    max_num = 15

    def view_ratio(self, instance):
        return instance.view_ratio * 100

    def click_ratio(self, instance):
        return instance.click_ratio * 100


class SupporterPromoAdmin(admin.ModelAdmin):
    model = SupporterPromo
    list_display = ('name', 'display_type', 'text', 'live', 'view_ratio', 'click_ratio')
    list_filter = ('live', 'display_type')
    inlines = [ImpressionInline]

    def view_ratio(self, instance):
        return instance.view_ratio() * 100

    def click_ratio(self, instance):
        return instance.click_ratio() * 100

admin.site.register(Supporter, SupporterAdmin)
admin.site.register(SupporterPromo, SupporterPromoAdmin)
admin.site.register(GeoFilter)
