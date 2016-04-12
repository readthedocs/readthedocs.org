from django.contrib import admin
from .models import (Supporter, SupporterPromo,
                     PromoImpressions, GeoFilter)


class GeoFilterAdmin(admin.ModelAdmin):
    model = GeoFilter
    filter_horizontal = ('countries',)


class GeoFilterInline(admin.TabularInline):
    model = GeoFilter
    filter_horizontal = ('countries',)
    extra = 0


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
    list_display = ('name', 'display_type', 'live',
                    'click_ratio', 'sold_impressions', 'total_views')
    list_filter = ('live', 'display_type')
    readonly_fields = ('total_views',)
    inlines = [ImpressionInline, GeoFilterInline]

    def view_ratio(self, instance):
        return instance.view_ratio() * 100

    def click_ratio(self, instance):
        return instance.click_ratio() * 100

    def total_views(self, instance):
        return sum(imp.views for imp in instance.impressions.all())

admin.site.register(Supporter, SupporterAdmin)
admin.site.register(SupporterPromo, SupporterPromoAdmin)
admin.site.register(GeoFilter, GeoFilterAdmin)
