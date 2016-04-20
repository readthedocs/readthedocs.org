"""Django admin interface for core models.
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from readthedocs.core.views import SendEmailView
from readthedocs.core.models import UserProfile
from readthedocs.projects.models import Project


class UserProjectInline(admin.TabularInline):
    model = Project.users.through
    verbose_name = 'User project'
    verbose_name_plural = 'User projects'
    extra = 1


class UserAdminExtra(UserAdmin):
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'is_staff', 'is_banned')
    actions = ['ban_user', 'send_email']
    inlines = [UserProjectInline]

    def is_banned(self, obj):
        return hasattr(obj, 'profile') and obj.profile.banned

    is_banned.short_description = 'Banned'

    def ban_user(self, request, queryset):
        users = []
        for profile in UserProfile.objects.filter(user__in=queryset):
            profile.banned = True
            profile.save()
            users.append(profile.user.username)
        self.message_user(request, 'Banned users: %s' % ', '.join(users))

    ban_user.short_description = 'Ban user'

    def send_email(self, request, queryset):
        view = SendEmailView.as_view()
        return view(request, queryset=queryset)

    send_email.short_description = 'Email user'


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'homepage')
    search_fields = ('user__username', 'homepage')
    raw_id_fields = ('user',)


admin.site.unregister(User)
admin.site.register(User, UserAdminExtra)
admin.site.register(UserProfile, UserProfileAdmin)
