"""Admin interface for subscription models."""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Q
from django.utils import timezone
from django.utils.html import format_html

from readthedocs.core.history import ExtraSimpleHistoryAdmin
from readthedocs.subscriptions.models import Plan, PlanFeature, Subscription


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature


class PlanAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = (
        'name',
        'slug',
        'price',
        'trial',
        'published',
    )
    filter_horizontal = ('for_organizations',)
    inlines = (PlanFeatureInline,)


class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ('get_feature_type_display', 'plan')
    list_select_related = ('plan',)
    search_fields = ('plan__name', 'feature_type')


class SubscriptionDateFilter(admin.SimpleListFilter):

    """Filter for the status of the subscriptions related to their date."""

    title = 'subscription date'
    parameter_name = 'subscription_date'

    TRIALING = 'trialing'
    TRIAL_ENDING = 'trial_ending'
    TRIAL_ENDED = 'trial_ended'
    EXPIRED = 'expired'

    def lookups(self, request, model_admin):
        return (
            (self.TRIALING, 'trial active'),
            (self.TRIAL_ENDING, 'trial ending'),
            (self.TRIAL_ENDED, 'trial ended'),
            (self.EXPIRED, 'subscription expired'),
        )

    def queryset(self, request, queryset):
        trial_queryset = (
            queryset.filter(
                Q(status='trialing') |
                Q(status__isnull=True),
            ),
        )  # yapf: disabled
        if self.value() == self.TRIALING:
            return trial_queryset.filter(trial_end_date__gt=timezone.now(),)
        if self.value() == self.TRIAL_ENDING:
            return trial_queryset.filter(
                trial_end_date__lt=timezone.now() + timedelta(days=7),
                trial_end_date__gt=timezone.now(),
            )
        if self.value() == self.TRIAL_ENDED:
            return trial_queryset.filter(trial_end_date__lt=timezone.now(),)
        if self.value() == self.EXPIRED:
            return queryset.filter(end_date__lt=timezone.now())


class SubscriptionAdmin(ExtraSimpleHistoryAdmin):
    model = Subscription
    list_display = ('organization', 'plan', 'status', 'stripe_subscription', 'trial_end_date')
    list_filter = ('status', SubscriptionDateFilter, 'plan')
    list_select_related = ('organization', 'plan')
    raw_id_fields = ('organization',)
    readonly_fields = ('stripe_subscription',)
    search_fields = ('organization__name', 'stripe_id')

    # pylint: disable=no-self-use
    def stripe_subscription(self, obj):
        if obj.stripe_id:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                "https://dashboard.stripe.com/subscriptions/{}".format(obj.stripe_id),
                obj.stripe_id,
            )
        return None


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(PlanFeature, PlanFeatureAdmin)
