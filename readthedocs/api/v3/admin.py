from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from readthedocs.api.v3.models import RTDToken


@admin.register(RTDToken)
class RTDTokenAdmin(admin.ModelAdmin):
    raw_id_fields = ["project", "created_by"]
    list_display = [
        "prefix",
        "name",
        "project",
        "created",
        "expires_at",
        "has_expired",
        "revoked_at",
    ]
    list_filter = ["created"]
    search_fields = ["name", "prefix", "project__slug"]
    readonly_fields = ["prefix", "revoked_at"]
    actions = ["revoke"]

    @admin.display(boolean=True, description=_("Has expired"))
    def has_expired(self, obj):
        return obj.has_expired

    @admin.action(description=_("Revoke selected API tokens"))
    def revoke(self, request, queryset):
        for token in queryset:
            token.revoke()

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        if not obj.created_by:
            obj.created_by = request.user
        key = RTDToken.objects.assign_key(obj)
        super().save_model(request, obj, form, change)
        messages.warning(
            request,
            _(
                "The API token for {name} is: {key}. "
                "Store it somewhere safe, you won't be able to see it again."
            ).format(name=obj.name, key=key),
        )
