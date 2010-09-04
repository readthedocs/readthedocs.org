<<<<<<< HEAD
"""Django admin interface for core models.
"""

=======
>>>>>>> FETCH_HEAD
from django.contrib import admin

from core.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserProfile, UserProfileAdmin)

