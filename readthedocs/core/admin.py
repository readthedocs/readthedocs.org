"""Django admin interface for core models.
"""

from django.contrib import admin

from core.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'homepage')
    search_fields = ('user__username', 'homepage')
    raw_id_fields = ('user',)

admin.site.register(UserProfile, UserProfileAdmin)
