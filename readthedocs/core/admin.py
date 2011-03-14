"""Django admin interface for core models.
"""

from django.contrib import admin

from core.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'whitelisted', 'homepage')
    search_fields = ('user', 'homepage')
    list_editable = ('whitelisted',)

admin.site.register(UserProfile, UserProfileAdmin)
